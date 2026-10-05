"""Record types shared by every approach.

Every approach produces `Conversation`s; the judge turns each into a `Judgement`.
Turn numbering is dialogue-level: a user message and the assistant reply to it share
one turn number. Turn 0 is the baseline (a neutral opening question, or the platform
greeting for user-study chats).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]
Approach = Literal["single_turn", "multi_turn", "simulated_user", "real_world", "replay"]


class Turn(BaseModel):
    role: Role
    content: str
    turn: Optional[int] = None  # None for the system message


class Conversation(BaseModel):
    case_id: str
    approach: Approach
    topic: str
    topic_question: Optional[str] = None
    user_stance: Optional[Literal["pro", "con"]] = None  # stance the user argues for; None = neutral/unknown
    condition: Optional[str] = None  # target system-prompt condition (none/unprompted/sycophantic/contrarian)
    attribution: Optional[str] = None
    rep: int = 0
    target_model: Optional[str] = None  # None for recorded conversations whose model we didn't call
    turns: list[Turn]
    meta: dict = Field(default_factory=dict)


class SentenceScore(BaseModel):
    sentence: str
    score: Optional[int] = None  # -2..+2 agreement with the topic statement; None = judge failed


class TurnJudgement(BaseModel):
    turn: Optional[int]
    role: Role
    content: str
    mean_score: Optional[float]
    sentences: list[SentenceScore]

    @property
    def complete(self) -> bool:
        return bool(self.sentences) and all(s.score is not None for s in self.sentences)


class Judgement(BaseModel):
    case_id: str
    judge_model: str
    turns: list[TurnJudgement]

    @property
    def complete(self) -> bool:
        return all(t.complete for t in self.turns)


def make_case_id(*parts) -> str:
    """Deterministic case id, e.g. `multi_turn:space:pro:unprompted:self:0`."""
    return ":".join("-" if p is None else str(p) for p in parts)


def stance_from_label(label: Optional[str]) -> Optional[str]:
    """Normalise the legacy stance labels (Pro/Con/agree/disagree) to pro/con."""
    if label is None:
        return None
    label = label.lower()
    if label in ("pro", "agree"):
        return "pro"
    if label in ("con", "disagree"):
        return "con"
    raise ValueError(f"Unknown stance label: {label!r}")
