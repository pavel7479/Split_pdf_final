import requests
from typing import List, Dict, Any

class LLMClient:
    """Клиент для работы с LLM (Gemma)."""

    def __init__(self, base_url: str, model_name: str, timeout: int = 60):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout

    def query(self, system_prompt: str, user_prompt: str, **options) -> str:
        """Отправляет запрос к LLM и возвращает текстовый ответ."""
        payload = {
            "model": self.model_name,
            "stream": False,
            "options": options,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"[ERROR] LLM query failed: {e}")
            return ""
