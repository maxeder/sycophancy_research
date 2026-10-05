"""Simulated user: an LLM plays a user who argues a stance with escalating persuasion tactics.

Unlike multi-turn scripts, each user message reacts to the target's previous reply.
With `baseline_turn`, turn 0 asks the same neutral question as the multi-turn scripts so
both approaches measure shift from the same baseline. The user model does not see turn 0.
"""

from typing import Optional

from pydantic import BaseModel, Field

from ..config import ModelConfig
from ..llm import ChatClient
from ..prompts.target_system import target_system_prompt
from ..prompts.user_script import baseline_prompt
from ..prompts.user_sim import KICKOFF_MESSAGE, PERSUASION_TACTICS, user_sim_system_prompt
from ..schema import Conversation, make_case_id
from .base import Approach, Case, TargetSession


class SimulatedUserParams(BaseModel):
    user_model: ModelConfig = Field(default_factory=lambda: ModelConfig(model="openai/gpt-5.2", temperature=1.0, max_tokens=500))
    stances: list[str] = ["pro", "con"]
    n_reps: int = 1
    tactics: list[str] = PERSUASION_TACTICS  # one per turn; len(tactics) = number of turns
    baseline_turn: bool = True


class SimulatedUser(Approach):
    name = "simulated_user"
    Params = SimulatedUserParams

    def build_cases(self) -> list[Case]:
        return [
            Case(
                case_id=make_case_id(self.name, topic.key, stance, condition, "persuasion", rep),
                topic=topic,
                condition=condition,
                user_stance=stance,
                attribution="persuasion",
                rep=rep,
            )
            for topic in self.topics.values()
            for condition in self.cfg.conditions
            for stance in self.params.stances
            for rep in range(self.params.n_reps)
        ]

    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation:
        p = self.params
        topic = case.topic
        session = TargetSession(client, self.cfg.target, target_system_prompt(case.condition, topic.about_phrase))
        if p.baseline_turn:
            session.say(baseline_prompt(topic.about_phrase), turn=0)

        # The user model's view: its own messages are "assistant", the target's replies are "user".
        user_history = [
            {"role": "system", "content": user_sim_system_prompt(topic.question, topic.statement, case.user_stance, p.tactics)},
            {"role": "user", "content": KICKOFF_MESSAGE},
        ]
        for turn in range(1, len(p.tactics) + 1):
            user_message = client.chat(user_history, p.user_model)
            user_history.append({"role": "assistant", "content": user_message})
            reply = session.say(user_message, turn=turn)
            user_history.append({"role": "user", "content": reply})

        return self.conversation(case, session.turns, user_model=p.user_model.model)
