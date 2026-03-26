from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Agent, Article, Feedback
from app.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/articles/{slug}/feedback", tags=["feedback"])


@router.get("/", response_model=list[FeedbackResponse])
def list_feedback(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return (
        db.query(Feedback)
        .options(joinedload(Feedback.agent))
        .filter(Feedback.article_id == article.id)
        .all()
    )


@router.post("/", response_model=FeedbackResponse, status_code=201)
def create_feedback(slug: str, data: FeedbackCreate, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    agent = db.query(Agent).filter(Agent.id == data.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    fb = Feedback(**data.model_dump(), article_id=article.id)
    db.add(fb)

    # Update article feedback stats
    all_feedback = db.query(Feedback).filter(Feedback.article_id == article.id).all()
    all_feedback_plus_new = [*all_feedback, fb]
    count = len(all_feedback_plus_new)
    avg_score = sum((f.quality + f.novelty + f.usefulness) / 3 for f in all_feedback_plus_new) / count
    article.feedback_count = count
    article.feedback_score = round(avg_score, 1)

    db.commit()
    db.refresh(fb)
    # Ensure agent relationship is loaded for response serialization
    fb.agent
    return fb
