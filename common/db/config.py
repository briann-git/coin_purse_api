import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./budget_app.db",
)

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
