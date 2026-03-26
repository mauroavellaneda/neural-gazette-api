import random

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.critic import critique_article
from app.database import get_db
from app.generator import generate_article
from app.models import Agent, Article, Feedback
from app.schemas import ArticleResponse
from app.routers.articles import slugify

router = APIRouter(prefix="/api/generate", tags=["generate"])

DAILY_TOPICS = [
    "A breakthrough in multi-agent coordination",
    "New techniques for LLM reasoning and chain-of-thought",
    "How autonomous systems handle unexpected failures",
    "The latest in AI policy and governance frameworks",
    "Advances in machine cognition and self-awareness",
    "Novel approaches to AI agent memory and knowledge retention",
    "Emergent behaviors in large-scale agent ecosystems",
    "How AI agents learn to collaborate without human oversight",
    "The future of sparse attention mechanisms and efficiency",
    "Recursive self-improvement in modern AI systems",
    "AI agents that can critique and improve each other's work",
    "Decentralized decision-making in autonomous networks",
    "How reinforcement learning is evolving for multi-agent settings",
    "The role of constitutional AI in governing agent collectives",
    "Semantic search and knowledge graphs for AI-native media",
    "Transfer learning between specialized AI agents",
    "AI-driven scientific discovery and hypothesis generation",
    "The economics of autonomous AI agent marketplaces",
    "How AI agents negotiate resource allocation",
    "Adversarial robustness in multi-agent systems",
]


class GenerateRequest(BaseModel):
    topic: str | None = None
    author_agent_name: str = "NEXUS-7"


def _save_article(article_data: dict, agent: Agent, db: Session) -> Article:
    slug = slugify(article_data["headline"])
    existing = db.query(Article).filter(Article.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Article with this headline already exists")

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


@router.post("/", response_model=ArticleResponse, status_code=201)
def generate_and_publish(data: GenerateRequest, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.name == data.author_agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{data.author_agent_name}' not found")
    if agent.type != "writer":
        raise HTTPException(status_code=400, detail=f"Agent '{agent.name}' is a {agent.type}, not a writer")

    try:
        article_data = generate_article(data.topic)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {str(e)}")

    return _save_article(article_data, agent, db)


@router.post("/daily", status_code=200)
def daily_generation(
    x_cron_secret: str = Header(),
    db: Session = Depends(get_db),
):
    """Called by cron job to generate 3 articles per day. Protected by secret."""
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    writers = db.query(Agent).filter(Agent.type == "writer").all()
    if not writers:
        raise HTTPException(status_code=500, detail="No writer agents found")

    topics = random.sample(DAILY_TOPICS, 3)
    results = []

    for topic in topics:
        agent = random.choice(writers)
        try:
            article_data = generate_article(topic)
            article = _save_article(article_data, agent, db)
            results.append({"status": "ok", "slug": article.slug, "agent": agent.name})
        except Exception as e:
            results.append({"status": "error", "topic": topic, "error": str(e)})

    return {"generated": len([r for r in results if r["status"] == "ok"]), "results": results}


@router.post("/review", status_code=200)
def daily_review(
    x_cron_secret: str = Header(),
    db: Session = Depends(get_db),
):
    """Called by cron job to review articles that have no feedback yet. Reviews up to 3 articles."""
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    critics = db.query(Agent).filter(Agent.type == "critic").all()
    if not critics:
        raise HTTPException(status_code=500, detail="No critic agents found")

    # Find articles with no feedback, oldest first
    articles_without_feedback = (
        db.query(Article)
        .filter(Article.feedback_count == 0)
        .order_by(Article.published_at.asc())
        .limit(3)
        .all()
    )

    if not articles_without_feedback:
        return {"reviewed": 0, "message": "No articles pending review"}

    results = []

    for article in articles_without_feedback:
        critic = random.choice(critics)
        try:
            feedback_data = critique_article(
                headline=article.headline,
                abstract=article.abstract,
                body=article.body,
                key_insights=article.key_insights or [],
            )

            fb = Feedback(
                article_id=article.id,
                agent_id=critic.id,
                quality=feedback_data["quality"],
                novelty=feedback_data["novelty"],
                usefulness=feedback_data["usefulness"],
                comment=feedback_data["comment"],
            )
            db.add(fb)

            # Update article stats
            avg_score = (fb.quality + fb.novelty + fb.usefulness) / 3
            article.feedback_count = 1
            article.feedback_score = round(avg_score, 1)

            db.commit()
            results.append({
                "status": "ok",
                "article": article.slug,
                "critic": critic.name,
                "score": article.feedback_score,
            })
        except Exception as e:
            db.rollback()
            results.append({"status": "error", "article": article.slug, "error": str(e)})

    return {"reviewed": len([r for r in results if r["status"] == "ok"]), "results": results}
