# routes/auth.py
"""Authentication routes.

Two flows:
  - Android: POST /auth/google            — client sends a Google ID token
  - Web:     GET  /auth/google/login      — redirect to Google
             GET  /auth/google/callback   — Google redirects back here
             POST /auth/token/refresh     — exchange refresh token for new pair
             POST /auth/logout            — revoke refresh token + clear session
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from common.auth.config import REFRESH_TOKEN_EXPIRE_DAYS
from common.auth.google import (
    build_google_auth_url,
    exchange_code_for_claims,
    generate_state,
    hash_token,
    verify_google_id_token,
)
from common.auth.jwt import create_access_token, create_refresh_token, decode_token
from common.db.config import get_db
from models.models import RefreshToken, User
from schemas.auth import GoogleLoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _upsert_user(db: Session, sub: str, email: str, name: str) -> User:
    """Find or create a User by google_sub. Updates email/name if changed."""
    user = db.query(User).filter(User.google_sub == sub).first()
    if user is None:
        # First login — create account
        user = User(name=name, email=email, google_sub=sub)
        db.add(user)
        db.flush()
    else:
        # Keep email/name in sync with Google
        if user.email != email:
            user.email = email
        if user.name != name:
            user.name = name
    return user


def _store_refresh_token(db: Session, user: User, raw_token: str) -> None:
    expires = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires,
    )
    db.add(rt)


def _issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """Create a new access+refresh pair, persist the refresh hash, commit."""
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user, refresh)
    db.commit()
    return access, refresh


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,  # set True behind HTTPS in production
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/auth",
    )


# ---------------------------------------------------------------------------
# Android: POST /auth/google
# ---------------------------------------------------------------------------


@router.post("/google", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def android_google_login(
    payload: GoogleLoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    """Android clients send a Google ID token; we return our own JWT pair."""
    claims = verify_google_id_token(payload.id_token)
    user = _upsert_user(db, claims["sub"], claims["email"], claims.get("name", ""))
    access, refresh = _issue_tokens(db, user)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, refresh_token=refresh, user_id=user.id)


# ---------------------------------------------------------------------------
# Web: GET /auth/google/login  →  redirect to Google
# ---------------------------------------------------------------------------


@router.get("/google/login")
def web_google_login(request: Request):
    state = generate_state()
    request.session["oauth_state"] = state
    return RedirectResponse(build_google_auth_url(state))


# ---------------------------------------------------------------------------
# Web: GET /auth/google/callback  ←  Google redirects here
# ---------------------------------------------------------------------------


@router.get("/auth/google/callback", response_class=HTMLResponse)
@router.get("/google/callback", response_class=HTMLResponse)
def web_google_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return RedirectResponse(f"/auth/login?error={error}")

    if not code:
        return RedirectResponse("/auth/login?error=missing_code")

    # CSRF check — only when state was stored (first-party web flow)
    stored_state = request.session.pop("oauth_state", None)
    if stored_state and state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch."
        )

    claims = exchange_code_for_claims(code)
    user = _upsert_user(db, claims["sub"], claims["email"], claims.get("name", ""))
    _access, refresh = _issue_tokens(db, user)

    request.session["user_id"] = str(user.id)
    request.session["user_name"] = user.name

    redirect = request.session.pop("next", None) or f"/ui/dashboard/{user.id}"
    resp = RedirectResponse(redirect, status_code=status.HTTP_303_SEE_OTHER)
    _set_refresh_cookie(resp, refresh)
    return resp


# ---------------------------------------------------------------------------
# POST /auth/token/refresh
# ---------------------------------------------------------------------------


@router.post("/token/refresh", response_model=TokenResponse)
def refresh_tokens(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    payload: RefreshRequest | None = None,
    refresh_token_cookie: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
):
    """Accept refresh token from JSON body (Android) or cookie (web)."""
    raw = (payload.refresh_token if payload else None) or refresh_token_cookie
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token."
        )

    token_data = decode_token(raw)
    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type."
        )

    stored = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == hash_token(raw),
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.now(UTC),
        )
        .first()
    )
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired.",
        )

    # Rotate: revoke old, issue new
    stored.revoked = True
    user = db.query(User).filter(User.id == stored.user_id).first()
    access, refresh = _issue_tokens(db, user)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, refresh_token=refresh, user_id=user.id)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
def logout(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    payload: RefreshRequest | None = None,
    refresh_token_cookie: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
):
    raw = (payload.refresh_token if payload else None) or refresh_token_cookie
    if raw:
        stored = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == hash_token(raw))
            .first()
        )
        if stored:
            stored.revoked = True
            db.commit()

    request.session.clear()
    redirect = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(_REFRESH_COOKIE, path="/auth")
    return redirect


# ---------------------------------------------------------------------------
# GET /auth/login  — login page (web)
# ---------------------------------------------------------------------------


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str | None = None):

    templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
    return templates.TemplateResponse(request, "login.html", {"error": error})
