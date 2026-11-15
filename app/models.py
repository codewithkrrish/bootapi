"""Request/response shapes for the API.

Kept separate from the store records on purpose: what the API accepts and
returns is a contract, what the database stores is an implementation detail.
"""

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """What a client sends to register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    """What the API returns about a user — never includes the password hash."""

    id: int
    email: str


class Token(BaseModel):
    """A login response: a bearer token and its type."""

    access_token: str
    token_type: str = "bearer"


class ItemCreate(BaseModel):
    """What a client sends to create an item."""

    title: str = Field(min_length=1, max_length=200)


class ItemPublic(BaseModel):
    """An item as the API returns it."""

    id: int
    title: str
    done: bool


class HealthStatus(BaseModel):
    """The /health response."""

    status: str
    app: str
    version: str
