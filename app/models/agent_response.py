from typing import Optional, List
from dataclasses import dataclass

@dataclass
class AgentResponse:
    text: str
    followup_question: Optional[str] = None
    suggested_intent: Optional[str] = None
    slots_to_fill: Optional[List[str]] = None
