from fastapi import FastAPI

from .core.database import Base, engine
from .models import user  # noqa: F401 - register model for create_all
from .routers import users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeet API")


@app.get("/")
def root():
    return {"message": "Meeet API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users.router)
