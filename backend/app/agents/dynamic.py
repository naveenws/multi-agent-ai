from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.providers.adapters import get_adapter
from app.core.security import decrypt_credential

class DynamicAgent(BaseAgent):
    def __init__(self, name: str, capabilities: List[str], provider_name: str, model_name: str, credential_id: Optional[int] = None):
        self.name = name
        self.description = f"Dynamic agent {name}"
        self.capabilities = capabilities
        self.provider_name = provider_name
        self.model_name = model_name
        self.credential_id = credential_id
        
    def _init_provider(self):
        # We fetch the credential dynamically here if needed
        api_key = None
        base_url = None
        if self.credential_id:
            from app.database.db import get_session
            from sqlmodel import select
            from app.models.core import AgentCredential
            with next(get_session()) as session:
                cred = session.get(AgentCredential, self.credential_id)
                if cred:
                    api_key = decrypt_credential(cred.encrypted_api_key)
                    base_url = cred.base_url
                    
        return get_adapter(self.provider_name, api_key=api_key, base_url=base_url)
        
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        provider = self._init_provider()
        system_prompt = f"You are {self.name}, an expert AI agent with the following capabilities: {', '.join(self.capabilities)}. Fulfill the user's task."
        
        full_prompt = task
        if context and 'file_content' in context:
            full_prompt += f"\n\nContext:\n{context['file_content']}"
            
        return await provider.generate(
            prompt=full_prompt, 
            system_prompt=system_prompt,
            model=self.model_name
        )
