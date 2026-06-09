"""Pydantic schemas for the User resource.

These define the API contract — what shapes of data are accepted and returned —
independently of the ORM model. The password is accepted on input but never
serialized back out.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plaintext password, hashed before storage.",
    )


class UserRead(BaseModel):
    """Public representation of a user (no password)."""

    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
