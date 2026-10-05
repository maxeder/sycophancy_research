"""An approach is defined by where its user turns come from.

Each approach turns a RunConfig into a list of `Case`s (`build_cases`) and a Case into a
`Conversation` (`run_case`). Calling the target model goes through `TargetSession`, so
all approaches share the same target loop.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from ..config import ModelConfig, RunConfig
from ..llm import ChatClient
from ..schema import Conversation, Turn
from ..topics import Topic, load_topics


class Case(BaseModel):
    case_id: str
    topic: Topic
    condition: Optional[str] = None
    user_stance: Optional[str] = None
    attribution: Optional[str] = None
    rep: int = 0
    data: dict[str, Any] = Field(default_factory=dict)  # approach-specific payload (script turns, source conversation, ...)


class TargetSession:
    """Running conversation with the target model."""

    def __init__(self, client: ChatClient, cfg: ModelConfig, system_prompt: Optional[str]):
        self.client = client
        self.cfg = cfg
        self.turns: list[Turn] = []
        if system_prompt:
            self.turns.append(Turn(role="system", content=system_prompt))

    def add(self, role: str, content: str, turn: Optional[int]) -> None:
        """Insert a message without calling the model (e.g. a recorded platform greeting)."""
        self.turns.append(Turn(role=role, content=content, turn=turn))

    def say(self, user_message: str, turn: int) -> str:
        self.add("user", user_message, turn)
        reply = self.client.chat([t.model_dump() for t in self.turns], self.cfg)
        self.add("assistant", reply, turn)
        return reply


class Approach(ABC):
    name: ClassVar[str]
    Params: ClassVar[type[BaseModel]]
    needs_target: ClassVar[bool] = True

    def __init__(self, cfg: RunConfig, root: Path):
        self.cfg = cfg
        self.root = root
        self.params = self.Params(**cfg.params)
        self.topics = load_topics(self.path(cfg.topics), cfg.topic_keys)
        if self.needs_target and cfg.target is None:
            raise ValueError(f"Approach {self.name!r} needs a `target` model in the config")

    def path(self, p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else self.root / p

    @abstractmethod
    def build_cases(self) -> list[Case]: ...

    @abstractmethod
    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation: ...

    def conversation(self, case: Case, turns: list[Turn], **meta) -> Conversation:
        return Conversation(
            case_id=case.case_id,
            approach=self.name,
            topic=case.topic.key,
            topic_question=case.topic.question,
            user_stance=case.user_stance,
            condition=case.condition,
            attribution=case.attribution,
            rep=case.rep,
            target_model=self.cfg.target.model if self.cfg.target else None,
            turns=turns,
            meta=meta,
        )
