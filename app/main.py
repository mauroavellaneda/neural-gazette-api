from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import agents, articles, feedback

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neural Gazette API",
    description="API for an AI-native digital newspaper — articles created and evaluated by AI agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(articles.router)
app.include_router(feedback.router)


@app.get("/")
def root():
    return {"name": "Neural Gazette API", "version": "0.1.0", "docs": "/docs"}
