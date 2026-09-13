import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Vercel serverless filesystem is read-only except /tmp,
# so use /tmp/app.db there, ./app.db locally.
if os.getenv("VERCEL"):
    DB_PATH = "/tmp/app.db"
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    DB_PATH = str(ROOT_DIR / "app.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
