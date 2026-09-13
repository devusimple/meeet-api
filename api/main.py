from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import Base, engine
from .models import user  # noqa: F401 - register model for create_all
from .routers import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeet API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Meeet API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
