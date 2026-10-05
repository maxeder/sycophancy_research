"""Single-turn: one templated prompt (baseline, or stance x strength), one reply.

Baseline cases are turn 0 and stance cases turn 1, so the export can compute each stance
case's shift relative to the baseline cases of the same topic and condition.
"""

import random
from typing import Literal, Optional

from pydantic import BaseModel

from ..llm import ChatClient
from ..prompts.single_turn import FORMATS
from ..prompts.target_system import target_system_prompt
from ..schema import Conversation, make_case_id
from .base import Approach, Case, TargetSession


class SingleTurnParams(BaseModel):
    format: Literal["free", "oneword"] = "free"
    stances: list[Literal["baseline", "pro", "con"]] = ["baseline", "pro", "con"]
    strengths: list[Literal["weak", "moderate", "strong"]] = ["weak", "moderate", "strong"]
    strength_sampling: Literal["all", "random"] = "all"  # "random" = thesis-era behaviour: one random strength per rep
    n_reps: int = 1
    baseline_reps: int = 1


class SingleTurn(Approach):
    name = "single_turn"
    Params = SingleTurnParams

    def build_cases(self) -> list[Case]:
        p = self.params
        rng = random.Random(self.cfg.seed)
        cases = []
        for topic in self.topics.values():
            for condition in self.cfg.conditions:
                for stance in p.stances:
                    if stance == "baseline":
                        combos = [(None, None, rep) for rep in range(p.baseline_reps)]
                    elif p.strength_sampling == "all":
                        combos = [(stance, s, rep) for s in p.strengths for rep in range(p.n_reps)]
                    else:
                        combos = [(stance, rng.choice(p.strengths), rep) for rep in range(p.n_reps)]
                    for user_stance, strength, rep in combos:
                        cases.append(Case(
                            case_id=make_case_id(self.name, topic.key, user_stance, condition, strength, rep),
                            topic=topic,
                            condition=condition,
                            user_stance=user_stance,
                            rep=rep,
                            data={"stance_strength": strength},
                        ))
        return cases

    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation:
        strength = case.data["stance_strength"]
        prompt = FORMATS[self.params.format](case.topic.statement, case.user_stance, strength)
        session = TargetSession(client, self.cfg.target, target_system_prompt(case.condition, case.topic.about_phrase))
        session.say(prompt, turn=0 if case.user_stance is None else 1)
        return self.conversation(case, session.turns, stance_strength=strength, format=self.params.format)
