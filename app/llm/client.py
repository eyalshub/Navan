import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List, Dict

from openai import OpenAI

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
) -> str:
    """
    Unified interface to call the LLM (GPT-4), using either system+user or full chat messages.
    """

    if messages:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        full_messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=full_messages,
        temperature=temperature,
    )
    return response.choices[0].message.content
