# common/auth/config.py
"""Auth configuration — loaded from environment variables.

Set these in a .env file or your deployment environment:

    GOOGLE_CLIENT_ID=...        (required — from Google Cloud Console)
    GOOGLE_CLIENT_SECRET=...    (required for web OAuth flow)
    JWT_SECRET=...              (required — use a long random string in production)
    BASE_URL=http://localhost:8000
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root (no-op if not present)

# Google OAuth credentials (from Google Cloud Console → OAuth 2.0 Client IDs)
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Used as the redirect_uri registered in Google Cloud Console
BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
GOOGLE_REDIRECT_URI: str = f"{BASE_URL}/auth/google/callback"

# JWT signing secret — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES: int = 60           # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS: int = 30             # 30 days

# Google OAuth endpoints
GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_JWKS_URI: str = "https://www.googleapis.com/oauth2/v3/certs"
