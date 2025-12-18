#app/orchestrator/extraction.py
import json
from typing import Dict, Any

from app.llm.client import call_llm
from app.llm.utils import load_prompt

EXTRACTION_PROMPT = load_prompt("prompts/extraction.yaml")["system"]


def extract_information(user_message: str) -> Dict[str, Any]:
    """
    Extract structured information from the user's message.
    Returns a dict (parsed JSON).
    """

    response_text = call_llm(
        system_prompt=EXTRACTION_PROMPT,
        user_prompt=user_message,
        temperature=0.0,
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: return empty extraction if LLM output is malformed
        return {}
