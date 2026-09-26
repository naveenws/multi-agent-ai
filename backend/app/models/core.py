from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON

def utcnow():
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    
class AgentCredential(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    encrypted_api_key: Optional[str] = None
    base_url: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
class AgentBase(SQLModel):
    name: str
    provider: str
    model: str
    credential_id: Optional[int] = Field(default=None, foreign_key="agentcredential.id")
    priority: int = 1
    cost_per_request: float = 0.0
    average_latency: float = 0.0
    success_rate: float = 100.0
    quality_score: float = 1.0
    is_active: bool = True

class Agent(AgentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    capabilities: List["AgentCapability"] = Relationship(back_populates="agent")

class AgentCapability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    capability_name: str
    
    agent: Agent = Relationship(back_populates="capabilities")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    original_prompt: str
    task_type: Optional[str] = None
    complexity: Optional[str] = None
    status: str = Field(default="pending") # pending, analyzing, planning, executing, evaluating, synthesizing, completed, failed
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
class TaskStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    step_order: int
    description: str
    required_capability: str
    status: str = Field(default="pending")
    
class AgentExecution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    agent_id: int = Field(foreign_key="agent.id")
    step_id: Optional[int] = Field(default=None, foreign_key="taskstep.id")
    prompt: str
    response: Optional[str] = None
    latency: Optional[float] = None
    status: str = Field(default="started") # started, completed, failed
    created_at: datetime = Field(default_factory=utcnow)
    
class Evaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    execution_id: int = Field(foreign_key="agentexecution.id")
    quality_score: float
    completeness_score: float
    relevance_score: float
    confidence: float
    has_major_errors: bool
    needs_retry: bool
    issues: str = Field(default="[]") # JSON list of issues
    created_at: datetime = Field(default_factory=utcnow)
    
class AgentFailure(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    execution_id: int = Field(foreign_key="agentexecution.id")
    error_message: str
    is_fallback_triggered: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    
class FinalResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    response_text: str
    created_at: datetime = Field(default_factory=utcnow)
