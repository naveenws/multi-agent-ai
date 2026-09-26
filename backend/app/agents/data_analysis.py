from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.providers.llm import get_default_provider

class DataAnalysisAgent(BaseAgent):
    name = "Data Analysis Agent"
    description = "Specializes in data analysis, statistics, and data interpretation."
    capabilities = ["data analysis", "statistics", "reasoning", "csv interpretation"]
    
    def __init__(self):
        self.provider = get_default_provider()
        
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        system_prompt = (
            "You are an expert Data Analysis Agent. Your goal is to analyze data, "
            "calculate statistics, interpret data files (like CSVs), and provide logical reasoning "
            "about data trends and anomalies."
        )
        
        full_prompt = task
        if context and 'file_content' in context:
             full_prompt += f"\n\nData Context:\n{context['file_content']}"
            
        return await self.provider.generate(prompt=full_prompt, system_prompt=system_prompt)
