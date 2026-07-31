import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://forge:forge@localhost:5432/researchforge")

# SQLite (used for the e2e dev-seed DB) opens one connection per thread by
# default; FastAPI serves requests (and BackgroundTasks) off a thread pool,
# so that default would raise "SQLite objects created in a thread can only
# be used in that same thread". Postgres doesn't have or need this option.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
