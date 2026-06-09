"""Authentication routes: registration and login."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: UserCreate, db: DbSession) -> UserRead:
    """Create a new account.

    Returns 409 if the email is already registered.
    """
    if user_crud.get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    user = user_crud.create_user(db, payload)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain a JWT access token",
)
def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Exchange credentials for a bearer token.

    Uses the OAuth2 password form (`username` + `password`); `username` is the
    user's email. Returns 401 on bad credentials.
    """
    user = user_crud.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current authenticated user",
)
def read_current_user(current_user: CurrentUser) -> UserRead:
    """Return the profile of the user owning the supplied token."""
    return current_user
