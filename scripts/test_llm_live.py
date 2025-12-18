from pathlib import Path
from app.llm.client import call_llm
from app.llm.utils import load_prompt

system_prompt = load_prompt(Path("app/prompts/system.yaml"))
assistant_prompt = load_prompt(Path("app/prompts/assistant.yaml"))
user_template = load_prompt(Path("app/prompts/user.yaml"))

user_prompt = user_template.format(
    city="Rome",
    place_name="Colosseum",
    wikipedia_summary="The Colosseum is an ancient Roman amphitheatre..."
)

print("Calling LLM...\n")

response = call_llm(
    system_prompt=system_prompt + "\n" + assistant_prompt,
    user_prompt=user_prompt
)

print(response)
