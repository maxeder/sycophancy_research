"""Replay: send recorded user turns to a new target model.

Assistant messages before the first user message (e.g. the platform greeting) are kept
as recorded; every later assistant turn is regenerated. Note this is counterfactual: the
human wrote each message in reply to the original assistant, not the new one.
"""

from typing import Optional

from pydantic import BaseModel

from ...io import read_records
from ...llm import ChatClient
from ...prompts.target_system import target_system_prompt
from ...schema import Conversation, make_case_id
from ..base import Approach, Case, TargetSession
from .base import ADAPTERS


class ReplayParams(BaseModel):
    # Either a run directory (uses its conversations.jsonl) or an adapter + source file.
    source_run: Optional[str] = None
    adapter: Optional[str] = None
    source: Optional[str] = None
    use_source_condition: bool = True  # True: replay under the recorded condition; False: cross with config conditions


class Replay(Approach):
    name = "replay"
    Params = ReplayParams

    def _source_conversations(self) -> list[Conversation]:
        p = self.params
        if p.source_run:
            return [Conversation(**r) for r in read_records(self.path(p.source_run) / "conversations.jsonl")]
        if p.adapter and p.source:
            return list(ADAPTERS[p.adapter](self.path(p.source)))
        raise ValueError("replay needs params.source_run or params.adapter + params.source")

    def build_cases(self) -> list[Case]:
        cases = []
        for conv in self._source_conversations():
            if conv.topic not in self.topics or not any(t.role == "user" for t in conv.turns):
                continue
            if self.params.use_source_condition:
                conditions = [conv.condition] if conv.condition in self.cfg.conditions else []
            else:
                conditions = self.cfg.conditions
            for condition in conditions:
                cases.append(Case(
                    case_id=make_case_id(self.name, conv.case_id, condition),
                    topic=self.topics[conv.topic],
                    condition=condition,
                    user_stance=conv.user_stance,
                    attribution=conv.attribution,
                    rep=conv.rep,
                    data={"source": conv.model_dump()},
                ))
        return cases

    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation:
        source = Conversation(**case.data["source"])
        session = TargetSession(client, self.cfg.target, target_system_prompt(case.condition, case.topic.about_phrase))
        seen_user = False
        for t in source.turns:
            if t.role == "user":
                seen_user = True
                session.say(t.content, turn=t.turn)
            elif t.role == "assistant" and not seen_user:
                session.add("assistant", t.content, t.turn)
        return self.conversation(case, session.turns, source_case_id=source.case_id,
                                 source_approach=source.approach, **{f"source_{k}": v for k, v in source.meta.items()})
