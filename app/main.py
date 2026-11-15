"""Application factory and entry point.

`create_app()` builds the FastAPI app so tests can spin up a fresh one
against a throwaway database. `run()` is the console-script entry point
(`bootapi` after `pip install .`).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .config import get_settings
from .routers import auth, health, items
from .store import Store


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the tables on startup. Nothing else to warm up yet."""
    settings = get_settings()
    Store(settings.database_path).init_db()
    yield


def create_app() -> FastAPI:
    """Build the app with all routers mounted."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A FastAPI starter template — JWT auth, settings, SQLite store, "
            "and tests included. Clone it and build your API on top."
        ),
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(items.router)
    return app


app = create_app()


def run() -> None:
    """Start the dev server. `bootapi` on the command line runs this."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
