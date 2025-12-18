import yaml
from pathlib import Path



def load_prompt(relative_path: str) -> dict:
    base_dir = Path(__file__).resolve().parents[1]  # app/
    prompt_path = base_dir / relative_path

    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
