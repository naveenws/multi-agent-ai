from typing import List, Dict, Type
from app.agents.base import BaseAgent
from app.agents.research import ResearchAgent
from app.agents.data_analysis import DataAnalysisAgent
from app.agents.coding import CodingAgent
from app.agents.critic import CriticAgent
from app.agents.synthesizer import SynthesisAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(ResearchAgent())
        self.register(DataAnalysisAgent())
        self.register(CodingAgent())
        self.register(CriticAgent())
        self.register(SynthesisAgent())
        
    def register(self, agent: BaseAgent):
        self._agents[agent.name] = agent
        
    def get_agent(self, name: str) -> BaseAgent:
        return self._agents.get(name)
        
    def get_all_agents(self) -> List[BaseAgent]:
        return list(self._agents.values())
        
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        return [
            agent for agent in self._agents.values() 
            if capability.lower() in [cap.lower() for cap in agent.capabilities]
        ]

agent_registry = AgentRegistry()
