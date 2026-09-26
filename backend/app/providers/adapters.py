import os
import time
import httpx
from typing import Dict, Any, List, Optional
from google import genai
import google.genai.types as genai_types
import openai
from app.providers.base import BaseProvider

class GeminiAdapter(BaseProvider):
    def _get_client(self):
        key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("No API key provided for Gemini")
        return genai.Client(api_key=key)

    async def validate_credentials(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False

    async def get_models(self) -> List[str]:
        # Simple hardcoded list for now, realistically fetched via API
        return ["gemini-3.8-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

    async def test_connection(self) -> Dict[str, Any]:
        start = time.time()
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents="Ping."
            )
            return {"success": True, "latency": time.time() - start, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "latency": time.time() - start, "message": str(e)}

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, **kwargs) -> str:
        client = self._get_client()
        use_model = model or "gemini-3.8-flash"
        contents = []
        if system_prompt:
             contents.append(
                 genai_types.Content(
                     role="user",
                     parts=[genai_types.Part.from_text(text=f"System Instructions: {system_prompt}\n\nTask: {prompt}")]
                 )
             )
        else:
             contents.append(
                 genai_types.Content(
                     role="user",
                     parts=[genai_types.Part.from_text(text=prompt)]
                 )
             )
             
        response = client.models.generate_content(model=use_model, contents=contents)
        return response.text
        
    async def get_capabilities(self, model: str) -> List[str]:
        return ["text", "vision", "tool_use"]


class OpenAIAdapter(BaseProvider):
    def _get_client(self):
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("No API key provided for OpenAI")
        return openai.AsyncOpenAI(api_key=key, base_url=self.base_url)

    async def validate_credentials(self) -> bool:
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception:
            return False

    async def get_models(self) -> List[str]:
        try:
            client = self._get_client()
            models = await client.models.list()
            # Don't filter by 'gpt', return all available models from the custom provider
            return [m.id for m in models.data]
        except Exception:
            return ["gpt-4o", "gpt-4o-mini"]

    async def test_connection(self) -> Dict[str, Any]:
        start = time.time()
        try:
            client = self._get_client()
            # Just listing models is the safest way to test API key validity
            # without charging tokens or guessing a model name that might not exist
            await client.models.list()
            return {"success": True, "latency": time.time() - start, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "latency": time.time() - start, "message": str(e)}

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, **kwargs) -> str:
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
        
    async def get_capabilities(self, model: str) -> List[str]:
        return ["text", "vision", "tool_use", "function_calling"]


class OllamaAdapter(BaseProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = self.base_url or "http://localhost:11434"

    async def validate_credentials(self) -> bool:
        return True # Local, no credentials required

    async def get_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    return [m['name'] for m in resp.json().get('models', [])]
        except Exception:
            pass
        return ["llama3", "mistral", "qwen"]

    async def test_connection(self) -> Dict[str, Any]:
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    return {"success": True, "latency": time.time() - start, "message": "Local server connected"}
        except Exception as e:
            return {"success": False, "latency": time.time() - start, "message": f"Cannot connect to local server: {str(e)}"}

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, **kwargs) -> str:
        use_model = model or "llama3"
        payload = {
            "model": use_model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=300)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            raise Exception(f"Ollama API Error: {resp.text}")
            
    async def get_capabilities(self, model: str) -> List[str]:
        return ["text", "local"]


def get_adapter(provider_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> BaseProvider:
    name = provider_name.lower()
    if "gemini" in name:
        return GeminiAdapter(api_key=api_key, base_url=base_url)
    elif "openai" in name:
        return OpenAIAdapter(api_key=api_key, base_url=base_url)
    elif "ollama" in name or "local" in name:
        return OllamaAdapter(api_key=api_key, base_url=base_url)
    else:
        # Fallback to OpenAI-compatible generic adapter
        return OpenAIAdapter(api_key=api_key, base_url=base_url)
