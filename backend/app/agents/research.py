from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.providers.llm import get_default_provider

class ResearchAgent(BaseAgent):
    name = "Research Agent"
    description = "Specializes in information gathering, summarization, and fact extraction."
    capabilities = ["information gathering", "summarization", "research", "fact extraction"]
    
    def __init__(self):
        self.provider = get_default_provider()
        
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        system_prompt = (
            "You are an expert Research Agent. Your goal is to gather information, "
            "summarize findings clearly, and extract key facts based on the user's request. "
            "Present your findings in a structured, readable format."
        )
        
        full_prompt = task
        if context and 'file_content' in context:
            full_prompt += f"\n\nContext/File Content:\n{context['file_content']}"
            
        return await self.provider.generate(prompt=full_prompt, system_prompt=system_prompt)
