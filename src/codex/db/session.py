from __future__ import annotations

from typing import Generator

from sqlmodel import Session, SQLModel, create_engine


def get_engine(database_url: str = "sqlite:///codex.db"):
    return create_engine(database_url, echo=False, future=True)


def init_db(database_url: str = "sqlite:///codex.db") -> None:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def get_session(database_url: str = "sqlite:///codex.db") -> Generator[Session, None, None]:
    engine = get_engine(database_url)
    with Session(engine) as session:
        yield session
