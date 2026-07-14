"""
LLM client — provider-agnostic wrapper.

Currently: OpenRouter (gpt-4o-mini)
Future: Ollama, Gemini, Claude
"""

import json
import os
from typing import Optional

import requests

from career_os.config_loader import load_config


class LLMClient:
    """Simple LLM client for structured generation."""

    def __init__(self):
        config = load_config()
        self.provider = config.get("llm", {}).get("provider", "openrouter")
        self.model = config.get("llm", {}).get("model", "openai/gpt-4o-mini")
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = config.get("llm", {}).get("base_url", "https://openrouter.ai/api/v1")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")

    def generate(
        self,
        prompt: str,
        system: str = "You are a career strategist applying the Evidence > Claim principle.",
        json_mode: bool = True,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate LLM response.

        Args:
            prompt: User prompt
            system: System message
            json_mode: If True, request JSON output
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            Raw response string (JSON if json_mode=True)
        """
        if self.provider == "openrouter":
            return self._call_openrouter(prompt, system, json_mode, temperature, max_tokens)
        raise ValueError(f"Provider '{self.provider}' not implemented yet")

    def _call_openrouter(self, prompt, system, json_mode, temperature, max_tokens) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://career-os.local",
            "X-Title": "CareerOS",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str, system: str = None) -> dict:
        """Generate and parse JSON response."""
        if system is None:
            system = "You are a career strategist. Always respond with valid JSON."

        raw = self.generate(prompt, system, json_mode=True)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        return json.loads(cleaned)


_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
