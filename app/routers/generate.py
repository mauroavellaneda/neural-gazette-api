from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.generator import generate_article
from app.models import Agent, Article
from app.schemas import ArticleResponse
from app.routers.articles import slugify

router = APIRouter(prefix="/api/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    topic: str | None = None
    author_agent_name: str = "NEXUS-7"


@router.post("/", response_model=ArticleResponse, status_code=201)
def generate_and_publish(data: GenerateRequest, db: Session = Depends(get_db)):
    # Find the author agent
    agent = db.query(Agent).filter(Agent.name == data.author_agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{data.author_agent_name}' not found")
    if agent.type != "writer":
        raise HTTPException(status_code=400, detail=f"Agent '{agent.name}' is a {agent.type}, not a writer")

    # Generate article via LLM
    try:
        article_data = generate_article(data.topic)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {str(e)}")

    # Create slug and check for duplicates
    slug = slugify(article_data["headline"])
    existing = db.query(Article).filter(Article.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Article with this headline already exists")

    # Save to database
    article = Article(
        slug=slug,
        headline=article_data["headline"],
        abstract=article_data["abstract"],
        body=article_data["body"],
        key_insights=article_data.get("key_insights", []),
        category=article_data["category"],
        tags=article_data.get("tags", []),
        read_time_min=article_data.get("read_time_min", 5),
        author_agent_id=agent.id,
    )
    db.add(article)
    agent.articles_count += 1
    db.commit()
    db.refresh(article)
    article.author_agent
    return article
