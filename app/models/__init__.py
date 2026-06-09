"""ORM models. Importing them here ensures they are registered on the
declarative `Base.metadata` before tables are created."""

from app.models.task import Task
from app.models.user import User

__all__ = ["User", "Task"]
