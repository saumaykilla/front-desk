"""Prompt loading."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system.md"


def load_system_prompt(*, local_date: str | None = None) -> str:
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"System prompt is empty: {SYSTEM_PROMPT_PATH}")
    if local_date is not None:
        prompt = f"{prompt}\n\nCurrent property-local date (America/New_York): {local_date}."
    return prompt
