from typing import List, Dict, Optional
from app.agents.base import BaseAgent
from app.agents.dynamic import DynamicAgent
from app.database.db import get_session
from app.models.core import Agent
from sqlmodel import select

class AgentSelector:
    def __init__(self):
        pass

    def select_agent(self, required_capabilities: List[str], excluded_agents: List[str] = None, excluded_providers: List[str] = None) -> Optional[BaseAgent]:
        """
        Dynamically selects the best agent based on capabilities from the Database.
        """
        if excluded_agents is None:
            excluded_agents = []
        if excluded_providers is None:
            excluded_providers = []
            
        with next(get_session()) as session:
            db_agents = session.exec(select(Agent).where(Agent.is_active == True)).all()
            
            available_agents = [a for a in db_agents if a.name not in excluded_agents and a.provider not in excluded_providers]
            
            best_agent = None
            highest_score = -999.0
            
            for agent in available_agents:
                # Load capabilities
                agent_caps = [c.capability_name for c in agent.capabilities]
                
                # Capability Match Score
                match_count = sum(1 for cap in required_capabilities if cap.lower() in [c.lower() for c in agent_caps])
                capability_match = match_count / len(required_capabilities) if required_capabilities else 1.0
                
                # Historical Quality (can be fetched dynamically, using defaults for now)
                quality_score = 0.90
                success_rate = 0.95
                priority = agent.priority
                
                score = (
                    capability_match * 0.50
                    + quality_score * 0.20
                    + success_rate * 0.20
                    + priority * 0.10
                )
                
                if score > highest_score and capability_match >= 0:
                    highest_score = score
                    best_agent = agent
                    
            if best_agent:
                agent_caps = [c.capability_name for c in best_agent.capabilities]
                return DynamicAgent(
                    name=best_agent.name,
                    capabilities=agent_caps,
                    provider_name=best_agent.provider,
                    model_name=best_agent.model,
                    credential_id=best_agent.credential_id
                )
            
            return None
