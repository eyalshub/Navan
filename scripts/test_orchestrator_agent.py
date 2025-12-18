import json
from app.agents.orchestrator_agent import OrchestratorAgent

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def assert_in(text: str, expected_keywords: list, context=""):
    assert any(k.lower() in text.lower() for k in expected_keywords), f"Assertion failed in context: {context}\nText: {text}"

def print_turn(role: str, text: str):
    print(f"\n[{role.upper()}] {text}")

def print_state(state):
    print("\n[STATE]")
    print(state)

def run_conversation(messages, expected_final_intent=None):
    orchestrator = OrchestratorAgent()
    for msg in messages:
        print_turn("user", msg)
        response = orchestrator.handle_message(msg)
        print_turn("assistant", response)

    if expected_final_intent:
        assert orchestrator.state.intent_hint == expected_final_intent, (
            f"Expected final intent '{expected_final_intent}', but got '{orchestrator.state.intent_hint}'"
        )
    return orchestrator


# --------------------------------------------------
# Simulation 1 – Explain a place (Happy Path)
# --------------------------------------------------

def test_explain_place():
    print("\n✅ TEST 1: Explain a known place")
    messages = [
        "Hi",
        "I'm in Barcelona near the Sagrada Família",
        "Can you explain this place to me?",
    ]
    orchestrator = run_conversation(messages, expected_final_intent=None)
    assert orchestrator.state.last_place_name.lower() in ["sagrada família", "sagrada familia"], "Place name incorrect"


# --------------------------------------------------
# Simulation 2 – Find attractions nearby
# --------------------------------------------------

def test_find_attractions():
    print("\n✅ TEST 2: Find attractions around known place")
    messages = [
        "Hi",
        "I'm in Barcelona near the Sagrada Família",
        "What can I do around here?",
    ]
    orchestrator = run_conversation(messages, expected_final_intent=None)
    assert orchestrator.state.last_lat is not None and orchestrator.state.last_lon is not None, "Missing coordinates"


# --------------------------------------------------
# Simulation 3 – Ambiguous intent (should not trigger)
# --------------------------------------------------

def test_ambiguous_intent():
    print("\n✅ TEST 3: Ambiguous user input should ask clarification")
    messages = [
        "Hi",
        "I'm near the Eiffel Tower",
        "Interesting place",
    ]
    orchestrator = run_conversation(messages)
    assert orchestrator.state.intent_hint is None, "Intent should not be set for vague message"


# --------------------------------------------------
# Simulation 4 – Switching intent mid-conversation
# --------------------------------------------------

def test_switch_intent():
    print("\n✅ TEST 4: Switch intent from explanation to attractions")
    messages = [
        "Hi",
        "I'm in Barcelona near the Sagrada Família",
        "Can you explain this place?",
        "Ok, what can I do around here?",
    ]
    orchestrator = run_conversation(messages)
    assert orchestrator.state.intent_hint is None, "Intent should be cleared after action"


# --------------------------------------------------
# Simulation 5 – Messy user behavior
# --------------------------------------------------

def test_messy_user():
    print("\n✅ TEST 5: Messy user conversation (incomplete, vague)")
    messages = [
        "Hey",
        "Barcelona",
        "near that big church",
        "what is this place?",
        "cool",
        "what else is around?",
    ]
    orchestrator = run_conversation(messages)
    assert orchestrator.state.last_city.lower() == "barcelona", "City should be inferred"
    assert orchestrator.state.intent_hint is None, "Intent should be cleared after full flow"


# --------------------------------------------------
# Run all tests
# --------------------------------------------------

if __name__ == "__main__":
    test_explain_place()
    test_find_attractions()
    test_ambiguous_intent()
    test_switch_intent()
    test_messy_user()

    print("\n=== ✅ All Orchestrator Tests Passed ===\n")
