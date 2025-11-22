from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from codax.config import DEFAULT_DATA_DIR


def _default_url() -> str:
    db_path = DEFAULT_DATA_DIR / "codax.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or _default_url()
    return create_engine(url, echo=False, future=True)


def init_db(database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def get_session(database_url: str | None = None) -> Generator[Session, None, None]:
    engine = get_engine(database_url)
    with Session(engine) as session:
        yield session
