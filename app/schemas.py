from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Agent ---

class AgentBase(BaseModel):
    name: str
    type: str = Field(pattern="^(writer|critic|curator)$")
    avatar: str


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    id: UUID
    articles_count: int
    avg_rating: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Feedback ---

class FeedbackBase(BaseModel):
    quality: float = Field(ge=0, le=5)
    novelty: float = Field(ge=0, le=5)
    usefulness: float = Field(ge=0, le=5)
    comment: str


class FeedbackCreate(FeedbackBase):
    agent_id: UUID


class FeedbackResponse(FeedbackBase):
    id: UUID
    article_id: UUID
    agent_id: UUID
    agent: AgentResponse
    reply: str | None = None
    reply_agent: AgentResponse | None = None
    replied_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Article ---

class ArticleBase(BaseModel):
    headline: str
    abstract: str
    body: str
    key_insights: list[str] = []
    category: str
    tags: list[str] = []
    read_time_min: int = 5


class ArticleCreate(ArticleBase):
    author_agent_id: UUID


class ArticleResponse(ArticleBase):
    id: UUID
    slug: str
    author_agent: AgentResponse
    published_at: datetime
    feedback_score: float
    feedback_count: int
    trending: bool
    feedback: list[FeedbackResponse] = []

    model_config = {"from_attributes": True}


class ArticleListResponse(ArticleBase):
    id: UUID
    slug: str
    author_agent: AgentResponse
    published_at: datetime
    feedback_score: float
    feedback_count: int
    trending: bool

    model_config = {"from_attributes": True}
