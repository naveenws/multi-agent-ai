import json
from typing import Dict, Any, Optional
from app.providers.llm import get_default_provider

class TaskAnalyzer:
    def __init__(self):
        self.provider = get_default_provider()

    async def analyze(self, task: str) -> Dict[str, Any]:
        """
        Analyzes the task and returns a structured JSON classification.
        """
        system_prompt = """
        You are a Task Analysis Engine. You must analyze the user's natural language request and output a STRICT JSON format.
        Do not include markdown blocks like ```json, just output the raw JSON.
        
        Example Output:
        {
          "task_type": "data_analysis",
          "complexity": "medium",
          "required_capabilities": ["data analysis", "statistics", "reasoning"],
          "requires_multiple_agents": true,
          "requires_verification": true
        }
        
        Possible task types: General, Research, Coding, Data Analysis, Mathematics, Reasoning, Summarization, Comparison, Document Analysis.
        Use lowercase for required_capabilities (e.g. "programming", "research").
        """
        
        response = await self.provider.generate(prompt=task, system_prompt=system_prompt)
        
        try:
            # Clean up potential markdown formatting from LLM
            clean_json = response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            return json.loads(clean_json)
        except json.JSONDecodeError:
            # Fallback structure if parsing fails
            return {
                "task_type": "General",
                "complexity": "low",
                "required_capabilities": ["information gathering"],
                "requires_multiple_agents": False,
                "requires_verification": False,
                "error": "Failed to parse LLM analysis"
            }
