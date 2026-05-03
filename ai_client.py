from abc import ABC, abstractmethod

from anthropic import Anthropic
from openai import OpenAI

SUMMARIZE_PROMPT = (
    "你是一个对话历史摘要助手。请将以下邮件对话历史压缩成一段简洁的中文摘要，"
    "保留关键信息、讨论要点和人物偏好。摘要应该简明扼要，不超过200字。"
)


class AIClient(ABC):
    @abstractmethod
    def generate_reply(self, system_prompt: str, user_message: str,
                       history: list[dict] | None = None) -> str:
        ...

    @abstractmethod
    def summarize_history(self, messages: list[dict]) -> str:
        ...


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, model_name: str, base_url: str | None = None,
                 max_tokens: int = 1024, temperature: float = 0.8):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    def generate_reply(self, system_prompt: str, user_message: str,
                       history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def summarize_history(self, messages: list[dict]) -> str:
        all_messages = [{"role": "system", "content": SUMMARIZE_PROMPT}]
        all_messages.extend(messages)
        response = self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=512,
            temperature=0.3,
            messages=all_messages,
        )
        return response.choices[0].message.content or ""


class AnthropicClient(AIClient):
    def __init__(self, api_key: str, model_name: str, base_url: str | None = None,
                 max_tokens: int = 1024, temperature: float = 0.8):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = Anthropic(**client_kwargs)

    def generate_reply(self, system_prompt: str, user_message: str,
                       history: list[dict] | None = None) -> str:
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text if response.content else ""

    def summarize_history(self, messages: list[dict]) -> str:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=512,
            temperature=0.3,
            system=SUMMARIZE_PROMPT,
            messages=messages,
        )
        return response.content[0].text if response.content else ""


def create_client(provider: str, api_key: str, model_name: str,
                  base_url: str | None = None, max_tokens: int = 1024,
                  temperature: float = 0.8) -> AIClient:
    if provider == "openai":
        return OpenAIClient(api_key, model_name, base_url, max_tokens, temperature)
    elif provider == "anthropic":
        return AnthropicClient(api_key, model_name, base_url, max_tokens, temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'.")
