from sqlalchemy import text
from sqlmodel import Field, SQLModel

from codax.db.session import get_engine, get_session, init_db


def test_init_db_creates_tables(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"

    class Sample(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)

    init_db(url)
    engine = get_engine(url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT name FROM sqlite_master"))
        assert result.fetchall()


def test_get_session_context_manager(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'session.db'}"
    init_db(url)
    session_gen = get_session(url)
    session = next(session_gen)
    assert session is not None
    # cleanly close generator
    try:
        next(session_gen)
    except StopIteration:
        pass
