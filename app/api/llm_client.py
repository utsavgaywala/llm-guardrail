"""
LLM Client — Using Groq (Free & Fast!)
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Load .env file locally — ignored on Railway (uses real env vars)
load_dotenv()


class LLMClient:

    def __init__(self):
        # Read directly from environment — works both locally and on Railway
        api_key = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found! Add it to .env file locally "
                "or as an environment variable on Railway."
            )
        self.client = Groq(api_key=api_key)
        self.model = os.environ.get("LLM_MODEL", "llama-3.1-8b-instant")
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