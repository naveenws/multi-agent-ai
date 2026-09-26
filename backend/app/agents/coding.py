from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.providers.llm import get_default_provider

class CodingAgent(BaseAgent):
    name = "Coding Agent"
    description = "Specializes in programming, debugging, code generation, and code explanation."
    capabilities = ["programming", "debugging", "code generation", "code explanation"]
    
    def __init__(self):
        self.provider = get_default_provider()
        
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        system_prompt = (
            "You are an expert Coding Agent. Your goal is to write clean, efficient, and well-documented code, "
            "debug issues, explain code snippets, and assist with software engineering tasks. "
            "Output your code using standard markdown code blocks."
        )
        
        full_prompt = task
        if context and 'file_content' in context:
             full_prompt += f"\n\nCode/File Context:\n{context['file_content']}"
            
        return await self.provider.generate(prompt=full_prompt, system_prompt=system_prompt)
