"""LLM Service

Wrapper for LLM API calls (OpenAI, Azure OpenAI, Anthropic) supporting structured JSON output.
"""

from typing import Any, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Service providing unified LLM invocation across agents."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def generate_structured(
        self, prompt: str, response_model: Type[T], system_prompt: str | None = None
    ) -> T | None:
        """
        Invoke the LLM with structured output enforcement (Pydantic schema).

        Args:
            prompt: User prompt.
            response_model: Expected Pydantic response class.
            system_prompt: System context instructions.

        Returns:
            Instantiated response_model or None.
        """
        # Placeholder for phase 3: OpenAI client.beta.chat.completions.parse(...)
        return None

    def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate raw text response from LLM.
        """
        # Placeholder for phase 3
        return ""
