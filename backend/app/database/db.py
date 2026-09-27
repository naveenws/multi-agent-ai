import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv

load_dotenv()

# We'll use sqlite for local development if postgres isn't running to make testing easier without docker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./multiagent.db")

# Fix for Render's default postgres:// URLs for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

def create_db_and_tables():
    from app.models.core import User, AgentCredential, Agent, AgentCapability, Task, TaskStep, AgentExecution, Evaluation, AgentFailure, FinalResponse
    try:
        SQLModel.metadata.create_all(engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # Re-raise so the app knows it can't start if the DB is required
        raise e
    
    with Session(engine) as session:
        # Check if agents exist
        from sqlmodel import select
        existing_agents = session.exec(select(Agent)).all()
        if not existing_agents:
            from app.orchestrator.registry import agent_registry
            for base_agent in agent_registry.get_all_agents():
                db_agent = Agent(
                    name=base_agent.name,
                    provider="Gemini", # Defaulting to Gemini for seed
                    model="gemini-3.8-flash",
                    is_active=True
                )
                session.add(db_agent)
                session.commit()
                session.refresh(db_agent)
                
                for cap in base_agent.capabilities:
                    db_cap = AgentCapability(agent_id=db_agent.id, capability_name=cap)
                    session.add(db_cap)
                session.commit()

def get_session():
    with Session(engine) as session:
        yield session
