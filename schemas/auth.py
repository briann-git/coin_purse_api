# schemas/auth.py
from __future__ import annotations

import uuid

from .common import APIModel


class GoogleLoginRequest(APIModel):
    """Android: client sends the Google ID token after Google Sign-In."""

    id_token: str


class TokenResponse(APIModel):
    """Returned to Android clients after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    user_id: uuid.UUID


class RefreshRequest(APIModel):
    refresh_token: str
