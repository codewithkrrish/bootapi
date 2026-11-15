"""The data layer. Plain sqlite3, no ORM.

A starter template doesn't need SQLAlchemy on day one — it needs a store you
can read in five minutes and swap out later without untangling anything.
Every method opens its own short-lived connection, so nothing is shared
across threads and a crashed request can't leave a half-written row behind.

Swap this file for a real database when you outgrow it; the routers only
talk to the Store methods, never to SQL directly.
"""

import sqlite3
from dataclasses import dataclass


class DuplicateEmailError(ValueError):
    """Raised when registering an email address that already exists."""


class NotFoundError(ValueError):
    """Raised when a requested record doesn't exist."""


@dataclass(frozen=True)
class UserRecord:
    """A user row, as stored (password hash included — never send it out)."""

    id: int
    email: str
    password_hash: str


@dataclass(frozen=True)
class ItemRecord:
    """An item row. Items exist to show the CRUD pattern, nothing more."""

    id: int
    owner_id: int
    title: str
    done: bool


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);
"""


class Store:
    """A tiny SQLite-backed store for users and their items."""

    def __init__(self, path: str) -> None:
        self._path = path
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create the tables if they don't exist yet. Safe to call twice."""
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def ping(self) -> bool:
        """Return True if the database answers a trivial query."""
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1").fetchone()
        except sqlite3.Error:
            return False
        return True

    # -- users ---------------------------------------------------------

    def create_user(self, email: str, password_hash: str) -> UserRecord:
        """Insert a user. Raises DuplicateEmailError on a taken email."""
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, password_hash),
                )
                user_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateEmailError(f"email {email!r} is already registered") from exc
        if user_id is None:  # pragma: no cover - sqlite always sets this
            raise RuntimeError("insert did not return a row id")
        return UserRecord(id=user_id, email=email, password_hash=password_hash)

    def get_user_by_email(self, email: str) -> UserRecord | None:
        """Return the user with this email, or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None:
            return None
        return UserRecord(
            id=row["id"], email=row["email"], password_hash=row["password_hash"]
        )

    def get_user_by_id(self, user_id: int) -> UserRecord | None:
        """Return the user with this id, or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return UserRecord(
            id=row["id"], email=row["email"], password_hash=row["password_hash"]
        )

    # -- items ---------------------------------------------------------

    def create_item(self, owner_id: int, title: str) -> ItemRecord:
        """Insert an item owned by ``owner_id``."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO items (owner_id, title) VALUES (?, ?)",
                (owner_id, title),
            )
            item_id = cur.lastrowid
        if item_id is None:  # pragma: no cover - sqlite always sets this
            raise RuntimeError("insert did not return a row id")
        return ItemRecord(id=item_id, owner_id=owner_id, title=title, done=False)

    def list_items(self, owner_id: int) -> list[ItemRecord]:
        """Return all items belonging to ``owner_id``, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, owner_id, title, done FROM items"
                " WHERE owner_id = ? ORDER BY id",
                (owner_id,),
            ).fetchall()
        return [
            ItemRecord(
                id=row["id"],
                owner_id=row["owner_id"],
                title=row["title"],
                done=bool(row["done"]),
            )
            for row in rows
        ]

    def get_item(self, item_id: int, owner_id: int) -> ItemRecord:
        """Return one item, or raise NotFoundError (also when it's not yours)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, owner_id, title, done FROM items"
                " WHERE id = ? AND owner_id = ?",
                (item_id, owner_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"item {item_id} not found")
        return ItemRecord(
            id=row["id"],
            owner_id=row["owner_id"],
            title=row["title"],
            done=bool(row["done"]),
        )

    def delete_item(self, item_id: int, owner_id: int) -> None:
        """Delete one item, or raise NotFoundError (also when it's not yours)."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM items WHERE id = ? AND owner_id = ?",
                (item_id, owner_id),
            )
        if cur.rowcount == 0:
            raise NotFoundError(f"item {item_id} not found")
