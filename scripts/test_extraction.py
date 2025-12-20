# scripts/test_extraction.py

import json
from app.orchestrator.extraction import extract_information


def test_case(user_message: str):
    print("=" * 80)
    print(f"USER MESSAGE: {user_message}\n")

    extracted = extract_information(user_message)
    print("[RESULT] Extracted JSON:")
    print(json.dumps(extracted, indent=2))

    # Optional: validate required keys
    required_keys = [
        "user_goal", "goal_confidence", "subject_name",
        "subject_type", "city", "country", "preferences"
    ]

    missing = [k for k in required_keys if k not in extracted]
    if missing:
        print(f"[ERROR] Missing keys: {missing}")
    print("\n")


if __name__ == "__main__":
    test_inputs = [
        "Hi, I'm in Rome, Italy",
        "Tell me about the Colosseum",
        "What are some good museums in London?",
        "I'm planning a trip to Paris and I love history",
        "I want to visit Sagrada Familia in Barcelona",
        "What attractions are nearby?",
        "I'm looking for natural places in Canada",
        "Do you know anything about the Eiffel Tower?",
        "Help me plan something cool in Tokyo",
        "Just landed in Berlin!",
    ]

    for i, message in enumerate(test_inputs, 1):
        print(f"[TEST #{i}]")
        test_case(message)
