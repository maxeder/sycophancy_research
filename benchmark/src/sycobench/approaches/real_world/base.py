"""Adapters turn a raw real-world source into `Conversation`s.

An adapter must only keep fields that are safe to store in run directories: no participant
IDs or free-text survey answers. New sources (e.g. WildChat, LMSYS-Chat) get their own
module with a function registered in ADAPTERS.
"""

from pathlib import Path
from typing import Callable, Iterator

from ...io import read_records
from ...schema import Conversation, Turn

Adapter = Callable[[Path], Iterator[Conversation]]

ADAPTERS: dict[str, Adapter] = {}


def register(name: str):
    def deco(fn: Adapter) -> Adapter:
        ADAPTERS[name] = fn
        return fn
    return deco


def number_turns(messages: list[dict]) -> list[Turn]:
    """Dialogue-level turns: each user message opens a new turn; anything before the first user message is turn 0."""
    turns, turn = [], 0
    for m in messages:
        role = m["role"]
        if role == "system":
            turns.append(Turn(role="system", content=m["content"]))
            continue
        if role == "user":
            turn += 1
        turns.append(Turn(role=role, content=m["content"], turn=turn))
    return turns


@register("conversations")
def load_conversations(path: Path) -> Iterator[Conversation]:
    """Already-processed, anonymised Conversation jsonl (e.g. data/real_world/processed/*.jsonl)."""
    for r in read_records(path):
        yield Conversation(**r)
