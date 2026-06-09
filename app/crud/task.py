"""Data-access functions for the Task model.

Every query is scoped by `owner_id` so a user can only ever see or mutate their
own tasks — ownership is enforced at the data layer, not just the route.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, owner_id: int, payload: TaskCreate) -> Task:
    task = Task(**payload.model_dump(), owner_id=owner_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> list[Task]:
    stmt = (
        select(Task)
        .where(Task.owner_id == owner_id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_task(db: Session, owner_id: int, task_id: int) -> Task | None:
    stmt = select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    return db.scalar(stmt)


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    """Apply a partial update; only provided fields are changed."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
