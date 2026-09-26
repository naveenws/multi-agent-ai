from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class TaskCreate(BaseModel):
    prompt: str
    
class TaskResponse(BaseModel):
    id: int
    original_prompt: str
    status: str
    created_at: datetime
    
class AgentResponse(BaseModel):
    id: int
    name: str
    capabilities: List[str]
    success_rate: float
    average_latency: float
    quality_score: float
    is_active: bool
