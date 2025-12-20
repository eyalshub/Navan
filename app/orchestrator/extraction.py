# app/orchestrator/extraction.py

import json
from typing import Dict, Any

from app.llm.client import call_llm
from app.llm.utils import load_prompt

PROMPT = load_prompt("prompts/extraction.yaml")  # returns dict with "system", "user", "assistant"


def normalize_extracted(raw: dict) -> dict:
    city_val = raw.get("city") or raw.get("location")
    if isinstance(city_val, dict):
        city = city_val.get("city")
        country = city_val.get("country")
    else:
        city = city_val
        country = raw.get("country")

    result = {
        "user_goal": raw.get("user_goal", None),
        "goal_confidence": raw.get("goal_confidence", 0.0),
        "subject_name": raw.get("subject_name") or raw.get("destination") or raw.get("attraction"),
        "subject_type": raw.get("subject_type") or raw.get("type") or raw.get("attraction_type"),
        "city": city,
        "country": country,
        "preferences": raw.get("preferences") or raw.get("interests", []),
    }

    # print("[DEBUG] normalized result:", result)
    return result


def extract_information(user_message: str) -> Dict[str, Any]:
    """
    Extract structured information from the user's message.
    """

    full_user_prompt = PROMPT["user"].replace("{message}", user_message)

    full_prompt = [
        {"role": "system", "content": PROMPT["system"]},
        {"role": "user", "content": full_user_prompt},
        {"role": "assistant", "content": PROMPT["assistant"]},
    ]

    # ⚠️ call_llm must support full messages list
    response_text = call_llm(messages=full_prompt, temperature=0.0)

    # print("[DEBUG] raw LLM extraction output:", response_text)

    try:
        json_start = response_text.find("{")
        if json_start != -1:
            response_text = response_text[json_start:]

        extracted = json.loads(response_text)

        # fallback: if only "destination" was returned
        if "destination" in extracted and "subject_name" not in extracted:
            extracted["subject_name"] = extracted["destination"]

        return normalize_extracted(extracted)

    except json.JSONDecodeError:
        print("[ERROR] Failed to parse JSON from extraction output")
        return {}
