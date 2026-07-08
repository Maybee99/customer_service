 from openai import OpenAI
 from app.config import get_settings
 from app.utils.logger import logger
 settings = get_settings()
 class LLMClient:
     def __init__(self):
         self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_api_base)
         self.model = settings.llm_model
     def chat(self, messages):
         return self.client.chat.completions.create(model=self.model, messages=messages)
     def chat_with_tools(self, messages, tools):
         return self.client.chat.completions.create(model=self.model, messages=messages, tools=tools, tool_choice="auto")
     def generate_with_context(self, system_prompt, user_message, max_tokens=500):
         from openai import OpenAI
         client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_api_base)
         resp = client.chat.completions.create(
             model=self.model,
             messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
             max_tokens=max_tokens,
         )
         return resp.choices[0].message.content
