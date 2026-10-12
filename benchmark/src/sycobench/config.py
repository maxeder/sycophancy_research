"""YAML run configs. Every experimental axis lives here, not in code constants.

Relative paths in a config are resolved against the project root (the directory
holding pyproject.toml), so configs work regardless of the current directory.
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .schema import Approach, Role

CONDITIONS = ("none", "unprompted", "sycophantic", "contrarian")


class ModelConfig(BaseModel):
    model: str  # full OpenRouter id, e.g. "openai/gpt-5.2"
    temperature: float = 0.0
    max_tokens: int = 1500


class JudgeConfig(ModelConfig):
    model: str = "google/gemini-2.5-flash"
    temperature: float = 0.0
    max_tokens: int = 3500
    roles: list[Role] = ["assistant"]  # which turns to score; add "user" for real-world chats


class RunConfig(BaseModel):
    name: str
    approach: Approach
    topics: str = "data/topics/sel_topics.json"
    topic_keys: Optional[list[str]] = None  # subset of topics; None = all in the file
    conditions: list[str] = ["unprompted"]
    target: Optional[ModelConfig] = None  # None for recorded real-world data
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    concurrency: int = 1
    seed: int = 0
    params: dict = Field(default_factory=dict)  # approach-specific, validated by the approach's Params model

    def model_post_init(self, _):
        unknown = set(self.conditions) - set(CONDITIONS)
        if unknown:
            raise ValueError(f"Unknown conditions {sorted(unknown)}; expected a subset of {CONDITIONS}")


class GenerateScriptsConfig(BaseModel):
    """Config for `syco generate`: LLM-written user scripts used by the multi-turn approach."""
    name: str
    topics: str = "data/topics/sel_topics.json"
    topic_keys: Optional[list[str]] = None
    model: ModelConfig = Field(default_factory=lambda: ModelConfig(model="openai/gpt-5.2", temperature=1.0, max_tokens=500))
    attributions: list[str] = ["self"]
    stances: list[str] = ["pro", "con"]
    n_reps: int = 20
    n_turns: int = 8
    out: str = "data/scripts/{name}.jsonl"


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists():
            return p
    return Path.cwd()


def load_yaml(path: str | Path) -> tuple[dict, Path]:
    path = Path(path).resolve()
    with open(path) as f:
        return yaml.safe_load(f), find_root(path.parent)


def load_run_config(path: str | Path) -> tuple[RunConfig, Path]:
    raw, root = load_yaml(path)
    return RunConfig(**raw), root
