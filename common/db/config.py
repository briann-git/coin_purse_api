
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.db import Base


engine = create_engine(
    "sqlite:///./budget_app.db",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




print("Database and tables created successfully.")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()