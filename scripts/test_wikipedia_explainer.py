from app.tools.wikipedia import get_wikipedia_summary
from app.agents.wikipedia_explainer_agent import (
    WikipediaExplainerAgent,
    WikipediaExplainerInput,
)
from app.guards.hallucination_guard import HallucinationGuard


def main():
    print("\n=== Wikipedia Explainer Agent – Manual Test ===\n")

    title = "Sagrada Família"
    print(f"Fetching Wikipedia summary for: {title}\n")

    summary = get_wikipedia_summary(title)

    if not summary.get("found"):
        print("❌ Wikipedia page not found")
        return

    print("=== Raw Wikipedia Summary ===")
    print(summary["summary"])
    print("\n" + "=" * 50 + "\n")

    agent = WikipediaExplainerAgent()

    agent_input = WikipediaExplainerInput(
        title=summary["title"],
        raw_summary=summary["summary"],
        user_style="friendly",
    )

    output = agent.run(agent_input)

    print("=== Agent Explanation ===\n")
    print(output.explanation)

    print("\n=== Key Points ===")
    for i, point in enumerate(output.key_points, 1):
        print(f"{i}. {point}")

    print("\n=== Follow-up Suggestions ===")
    for suggestion in output.followup_suggestions:
        print(f"- {suggestion}")

    guard = HallucinationGuard()
    issues = guard.validate(
        raw_summary=summary["summary"],
        agent_output=output.__dict__,
    )

    print("\n" + "=" * 50)
    print("=== Guard Validation ===")

    if not issues:
        print("✅ No hallucination issues detected.")
    else:
        print("⚠️ Potential issues detected:")
        for issue in issues:
            print(f"- {issue}")

    print("\n=== Test Completed ===\n")


if __name__ == "__main__":
    main()
