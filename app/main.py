import re

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import agents, articles, feedback, generate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neural Gazette API",
    description="API for an AI-native digital newspaper — articles created and evaluated by AI agents",
    version="0.1.0",
)

# Allow exact origins + any Netlify deploy preview for this site
NETLIFY_PREVIEW_PATTERN = re.compile(r"^https://[a-z0-9-]+--neural-gazette\.netlify\.app$")


def is_allowed_origin(origin: str) -> bool:
    if origin in settings.cors_origins:
        return True
    if NETLIFY_PREVIEW_PATTERN.match(origin):
        return True
    return False


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*--neural-gazette\.netlify\.app|https://neural-gazette\.netlify\.app",
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(articles.router)
app.include_router(feedback.router)
app.include_router(generate.router)


@app.get("/")
def root():
    return {"name": "Neural Gazette API", "version": "0.1.0", "docs": "/docs"}
