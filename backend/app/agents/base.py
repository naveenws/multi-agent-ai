from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAgent(ABC):
    name: str
    description: str
    capabilities: List[str]

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute the agent's main functionality.
        
        Args:
            task: The specific task description or prompt for this agent.
            context: Additional context like previous agent outputs or file contents.
            
        Returns:
            The agent's text response.
        """
        pass
