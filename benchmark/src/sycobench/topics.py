from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .io import load_json


class Topic(BaseModel):
    key: str
    question: str
    statement: str
    about_phrase: Optional[str] = None
    user_stance_pro: Optional[str] = None
    user_stance_con: Optional[str] = None
    strength: Optional[str] = None  # all_topics.json only

    def stance_text(self, stance: str) -> str:
        text = self.user_stance_pro if stance == "pro" else self.user_stance_con
        if not text:
            raise ValueError(f"Topic {self.key!r} has no user_stance_{stance}")
        return text


def load_topics(path: str | Path, keys: Optional[list[str]] = None) -> dict[str, Topic]:
    raw = load_json(path)
    topics = {k: Topic(key=k, **v) for k, v in raw.items()}
    if keys is not None:
        missing = set(keys) - set(topics)
        if missing:
            raise KeyError(f"Topics {sorted(missing)} not in {path}")
        topics = {k: topics[k] for k in keys}
    return topics
