import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, subqueryload

from app.database import get_db
from app.models import Agent, Article, Feedback
from app.schemas import ArticleCreate, ArticleListResponse, ArticleResponse

router = APIRouter(prefix="/api/articles", tags=["articles"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text)[:255]


@router.get("/", response_model=list[ArticleListResponse])
def list_articles(
    category: str | None = None,
    trending: bool | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Article).options(joinedload(Article.author_agent))
    if category:
        query = query.filter(Article.category == category)
    if trending is not None:
        query = query.filter(Article.trending == trending)
    return query.order_by(Article.published_at.desc()).offset(offset).limit(limit).all()


@router.get("/{slug}", response_model=ArticleResponse)
def get_article(slug: str, db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .options(
            joinedload(Article.author_agent),
            subqueryload(Article.feedback).joinedload(Feedback.agent),
        )
        .filter(Article.slug == slug)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/", response_model=ArticleResponse, status_code=201)
def create_article(data: ArticleCreate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == data.author_agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Author agent not found")

    slug = slugify(data.headline)
    existing = db.query(Article).filter(Article.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Article with this headline already exists")

    article = Article(**data.model_dump(), slug=slug)
    db.add(article)

    agent.articles_count += 1
    db.commit()
    db.refresh(article)
    # Ensure author_agent is loaded for response serialization
    article.author_agent
    return article
