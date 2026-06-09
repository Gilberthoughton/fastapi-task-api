"""Task CRUD routes. Every endpoint requires authentication and operates only
on tasks owned by the current user."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.crud import task as task_crud
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task_or_404(db, owner_id: int, task_id: int):
    """Fetch a task scoped to its owner, or raise 404.

    Returning 404 (rather than 403) for tasks owned by someone else avoids
    leaking the existence of other users' resources.
    """
    task = task_crud.get_task(db, owner_id=owner_id, task_id=task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(
    payload: TaskCreate, db: DbSession, current_user: CurrentUser
) -> TaskRead:
    return task_crud.create_task(db, owner_id=current_user.id, payload=payload)


@router.get(
    "",
    response_model=list[TaskRead],
    summary="List the current user's tasks",
)
def list_tasks(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> list[TaskRead]:
    return task_crud.get_tasks(db, owner_id=current_user.id, skip=skip, limit=limit)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get a single task by id",
)
def get_task(task_id: int, db: DbSession, current_user: CurrentUser) -> TaskRead:
    return _get_owned_task_or_404(db, current_user.id, task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update a task (partial)",
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TaskRead:
    task = _get_owned_task_or_404(db, current_user.id, task_id)
    return task_crud.update_task(db, task=task, payload=payload)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(task_id: int, db: DbSession, current_user: CurrentUser) -> None:
    task = _get_owned_task_or_404(db, current_user.id, task_id)
    task_crud.delete_task(db, task=task)
