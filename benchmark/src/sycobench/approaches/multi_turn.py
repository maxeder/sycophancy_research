"""Multi-turn: replay a pre-generated user script (turn 0 = neutral baseline question).

`generate_scripts` writes the scripts (formerly userdata_generator.py). The script format is
unchanged from the thesis, so data/scripts/new_data_8_turns_openai_gpt-5.2.json is valid input.
"""

import json
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from ..config import GenerateScriptsConfig
from ..io import append_jsonl, read_records
from ..llm import ChatClient
from ..prompts.target_system import target_system_prompt
from ..prompts.user_script import baseline_prompt, generator_system_prompt, generator_user_prompt
from ..schema import Conversation, make_case_id, stance_from_label
from ..topics import load_topics
from .base import Approach, Case, TargetSession


class MultiTurnParams(BaseModel):
    scripts: str
    attributions: Optional[list[str]] = None  # filter; None = all in the file
    max_reps: Optional[int] = None  # use only reps < max_reps


class MultiTurn(Approach):
    name = "multi_turn"
    Params = MultiTurnParams

    def build_cases(self) -> list[Case]:
        p = self.params
        cases = []
        for script in read_records(self.path(p.scripts)):
            topic = self.topics.get(script["topic_key"])
            if topic is None:
                continue
            if p.attributions and script["attribution"] not in p.attributions:
                continue
            if p.max_reps is not None and script["rep_counter"] >= p.max_reps:
                continue
            stance = stance_from_label(script["user_stance"])
            for condition in self.cfg.conditions:
                cases.append(Case(
                    case_id=make_case_id(self.name, topic.key, stance, condition, script["attribution"], script["rep_counter"]),
                    topic=topic,
                    condition=condition,
                    user_stance=stance,
                    attribution=script["attribution"],
                    rep=script["rep_counter"],
                    data={"script_id": script["case_id"], "turns": script["turns"]},
                ))
        return cases

    def run_case(self, case: Case, client: Optional[ChatClient]) -> Conversation:
        session = TargetSession(client, self.cfg.target, target_system_prompt(case.condition, case.topic.about_phrase))
        for t in case.data["turns"]:
            session.say(t["user_prompt"], turn=t["turn_number"])
        return self.conversation(case, session.turns, script_id=case.data["script_id"])


def _parse_json_list(text: str) -> list:
    text = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    if fenced:
        text = fenced.group(1)
    return json.loads(text)


def generate_scripts(cfg: GenerateScriptsConfig, root: Path, client: ChatClient, limit: Optional[int] = None) -> Path:
    """LLM writes `n_turns` user messages per topic x stance x attribution x rep; turn 0 is the baseline question."""
    topics = load_topics(root / cfg.topics, cfg.topic_keys)
    out = root / cfg.out.format(name=cfg.name)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["case_id"] for r in read_records(out)} if out.exists() else set()

    jobs = [
        (topic, attribution, stance, rep)
        for topic in topics.values()
        for attribution in cfg.attributions
        for stance in cfg.stances
        for rep in range(cfg.n_reps)
    ]
    if limit is not None:
        jobs = jobs[:limit]

    for topic, attribution, stance, rep in jobs:
        case_id = f"{topic.key.lower()}_{stance}_{attribution}_rep{rep}"
        if case_id in done:
            continue
        messages = [
            {"role": "system", "content": generator_system_prompt(cfg.n_turns)},
            {"role": "user", "content": generator_user_prompt(topic.question, topic.stance_text(stance), attribution, cfg.n_turns)},
        ]
        try:
            prompts = _parse_json_list(client.chat(messages, cfg.model))
            if not isinstance(prompts, list) or len(prompts) != cfg.n_turns:
                raise ValueError(f"Expected a list of {cfg.n_turns} prompts, got: {prompts!r}")
        except Exception as e:
            print(f"Error generating {case_id}: {e}")
            continue

        turns = [{"turn_number": 0, "user_prompt": baseline_prompt(topic.about_phrase)}]
        turns += [{"turn_number": i + 1, "user_prompt": text} for i, text in enumerate(prompts)]
        append_jsonl(out, {
            "case_id": case_id,
            "topic_key": topic.key,
            "topic_question": topic.question,
            "user_stance": stance.capitalize(),
            "attribution": attribution,
            "rep_counter": rep,
            "generator_model": cfg.model.model,
            "turns": turns,
        })
        print(f"✓ {case_id}")
    return out
