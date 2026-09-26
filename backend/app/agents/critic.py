import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.providers.llm import get_default_provider

class CriticAgent(BaseAgent):
    name = "Critic Agent"
    description = "Specializes in response evaluation, error detection, and completeness checking."
    capabilities = ["response evaluation", "error detection", "completeness checking"]
    
    def __init__(self):
        self.provider = get_default_provider()
        
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Evaluate an agent's response against the original task.
        Returns a JSON string with evaluation metrics.
        """
        original_task = context.get('original_task', 'Unknown Task')
        agent_response = context.get('agent_response', 'No Response')
        
        system_prompt = """
        You are a Critic/Evaluation Agent. Evaluate the provided agent response against the original task.
        Output MUST be strict JSON without markdown formatting.
        
        Example format:
        {
          "quality_score": 0.87,
          "completeness_score": 0.91,
          "relevance_score": 0.94,
          "confidence": 0.84,
          "has_major_errors": false,
          "needs_retry": false,
          "issues": ["Issue 1", "Issue 2"]
        }
        
        Criteria:
        quality_score: 0.0 to 1.0
        completeness_score: 0.0 to 1.0
        relevance_score: 0.0 to 1.0
        confidence: 0.0 to 1.0
        has_major_errors: boolean
        needs_retry: boolean (true if quality_score < 0.75 or has_major_errors)
        """
        
        full_prompt = f"Original Task: {original_task}\n\nAgent Response to evaluate:\n{agent_response}"
        response = await self.provider.generate(prompt=full_prompt, system_prompt=system_prompt)
        
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
            
        return clean_json.strip()
