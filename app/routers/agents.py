from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent
from app.schemas import AgentCreate, AgentResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/", response_model=list[AgentResponse])
def list_agents(agent_type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Agent)
    if agent_type:
        query = query.filter(Agent.type == agent_type)
    return query.order_by(Agent.name).all()


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: UUID, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentResponse, status_code=201)
def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    agent = Agent(**data.model_dump())
    db.add(agent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Agent with this name already exists")
    db.refresh(agent)
    return agent
