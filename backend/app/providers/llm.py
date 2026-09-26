import os
from abc import ABC, abstractmethod
from typing import Optional
from google import genai
import google.genai.types as genai_types
import openai
import anthropic

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.client:
            return "Mock Gemini Response: Gemini API key not found. Please configure GEMINI_API_KEY."
        
        try:
            model = kwargs.get("model", "gemini-3.8-flash")
            # Convert generation config logic if needed. For now simple generate_content
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

            response = self.client.models.generate_content(
                model=model,
                contents=contents,
            )
            return response.text
        except Exception as e:
            return f"Error from Gemini API: {str(e)}"

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.client:
            return "Mock OpenAI Response: OpenAI API key not found."
            
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "gpt-4o-mini"),
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI API: {str(e)}"

class MockProvider(LLMProvider):
    """Fallback provider when no keys are available"""
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return f"Mock response to: {prompt[:50]}... (Configure API keys to use real models)"

def get_default_provider() -> LLMProvider:
    if os.getenv("GEMINI_API_KEY"):
        return GeminiProvider()
    elif os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider()
    return MockProvider()
