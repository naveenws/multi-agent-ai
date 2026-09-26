from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseProvider(ABC):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def validate_credentials(self) -> bool:
        pass

    @abstractmethod
    async def get_models(self) -> List[str]:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Returns {'success': bool, 'latency': float, 'message': str}"""
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, **kwargs) -> str:
        pass
        
    @abstractmethod
    async def get_capabilities(self, model: str) -> List[str]:
        pass
        
    async def health_check(self) -> Dict[str, Any]:
        """Returns {'status': 'Available' | 'Error', 'message': str}"""
        try:
            res = await self.test_connection()
            if res.get('success'):
                return {"status": "Available", "message": "Connected"}
            return {"status": "Error", "message": res.get('message', 'Unknown error')}
        except Exception as e:
            return {"status": "Error", "message": str(e)}
