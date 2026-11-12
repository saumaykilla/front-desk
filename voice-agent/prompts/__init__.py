"""Prompt loading."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system.md"


def load_system_prompt() -> str:
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"System prompt is empty: {SYSTEM_PROMPT_PATH}")
    return prompt
