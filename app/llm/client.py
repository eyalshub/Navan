import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Calls OpenAI ChatCompletion with strict prompt control.
    Returns assistant text only.
    """

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()
