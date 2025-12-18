# scripts/test_wikipedia_explainer.py
from app.agents.wikipedia_explainer_agent import WikipediaExplainerAgent

def run_test():
    agent = WikipediaExplainerAgent()

    print("=== Wikipedia Explainer Test ===\n")

    subject = "Colosseum"
    city = "Rome"

    print(f"Testing subject: {subject}, city: {city}\n")

    result = agent.run(
        subject_name=subject,
        city=city,
    )

    print("=== Result ===")
    print(result)

if __name__ == "__main__":
    run_test()
