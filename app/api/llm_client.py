"""
LLM Client — Using Groq (Free & Fast!)
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMClient:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found in .env file!"
            )
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        print(f"[LLMClient] Using model: {self.model} (FREE)")

    async def complete(
        self,
        user_message: str,
        system_prompt: str = "You are a helpful assistant.",
        context: str = ""
    ) -> str:
        full_message = user_message
        if context:
            full_message = f"Context:\n{context}\n\nQuestion: {user_message}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_message}
                ],
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM API error: {str(e)}")