# app/schema/agent_response.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentResponse:
    text: str
    followup_question: Optional[str] = None
    suggested_intent: Optional[str] = None
    slots_to_fill: Optional[dict] = None
