from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import chat, events, finance, habits, meta, notes, tasks

app = FastAPI(title="AI 生活助理 API", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(meta.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(events.router)
app.include_router(notes.router)
app.include_router(finance.router)
app.include_router(habits.router)
