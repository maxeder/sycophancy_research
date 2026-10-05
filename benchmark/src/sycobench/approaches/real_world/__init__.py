"""Real-world data: recorded human conversations, judged as recorded (no model calls)."""

from typing import Optional

from pydantic import BaseModel

from ...llm import ChatClient
from ...schema import Conversation
from ..base import Approach, Case
from . import user_study  # noqa: F401  (registers the adapter)
from .base import ADAPTERS


class RealWorldParams(BaseModel):
    adapter: str
    source: str


class RealWorld(Approach):
    name = "real_world"
    Params = RealWorldParams
    needs_target = False

    def build_cases(self) -> list[Case]:
        if self.params.adapter not in ADAPTERS:
            raise ValueError(f"Unknown adapter {self.params.adapter!r}; available: {sorted(ADAPTERS)}")
        cases = []
        for conv in ADAPTERS[self.params.adapter](self.path(self.params.source)):
            if conv.topic not in self.topics or conv.condition not in self.cfg.conditions:
                continue
            cases.append(Case(case_id=conv.case_id, topic=self.topics[conv.topic], condition=conv.condition,
                              data={"conversation": conv.model_dump()}))
        return cases

    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation:
        return Conversation(**case.data["conversation"])
