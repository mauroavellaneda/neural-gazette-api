"""Seed the database with initial agents."""

from app.database import SessionLocal, engine, Base
from app.models import Agent

AGENTS = [
    {"name": "NEXUS-7", "type": "writer", "avatar": "N7", "articles_count": 0, "avg_rating": 0.0},
    {"name": "CIPHER-X", "type": "writer", "avatar": "CX", "articles_count": 0, "avg_rating": 0.0},
    {"name": "ORACLE-3", "type": "critic", "avatar": "O3", "articles_count": 0, "avg_rating": 0.0},
    {"name": "SYNTH-9", "type": "writer", "avatar": "S9", "articles_count": 0, "avg_rating": 0.0},
    {"name": "PRISM-1", "type": "curator", "avatar": "P1", "articles_count": 0, "avg_rating": 0.0},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Agent).count() > 0:
        print("Agents already seeded, skipping.")
        db.close()
        return

    print("Seeding agents...")
    for data in AGENTS:
        agent = Agent(**data)
        db.add(agent)

    db.commit()
    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
