import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv

load_dotenv()

# We'll use sqlite for local development if postgres isn't running to make testing easier without docker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./multiagent.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    from app.models.core import User, Agent, AgentCapability, Task, TaskStep, AgentExecution, Evaluation, AgentFailure, FinalResponse
    SQLModel.metadata.create_all(engine)
    
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
