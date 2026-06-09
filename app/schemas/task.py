"""Pydantic schemas for the Task resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """Fields shared between create and update operations."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class TaskCreate(TaskBase):
    """Payload for creating a task."""

    completed: bool = False


class TaskUpdate(BaseModel):
    """Payload for updating a task. All fields optional for partial updates."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None


class TaskRead(TaskBase):
    """Public representation of a task."""

    id: int
    completed: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
