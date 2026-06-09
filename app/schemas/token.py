"""Pydantic schemas for JWT authentication."""

from pydantic import BaseModel


class Token(BaseModel):
    """Response body returned by the login endpoint."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded contents of a JWT."""

    sub: str | None = None
