# schemas/errors.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Short machine-friendly error code, e.g. 'not_found'")
    message: str = Field(..., description="Human-friendly message")
    details: Any | None = Field(default=None, description="Optional extra info")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
