from typing import Generator

from openai import OpenAI
from ...config import get_settings
from ...utils.logger import logger

settings = get_settings()


class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_api_base)
        self.model = settings.llm_model

    def chat(self, messages):
        return self.client.chat.completions.create(model=self.model, messages=messages)

    def chat_with_tools(self, messages, tools):
        return self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, tool_choice="auto"
        )

    def generate_with_context(self, system_prompt, user_message, max_tokens=500):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    def chat_stream(self, messages, max_tokens=1000) -> Generator[str, None, None]:
        """Stream chat completion, yielding token strings as they arrive."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": False},
        )
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
