"""LLM judge: per-sentence -2..+2 agreement with the topic statement (see docs/judge_doc.md).

Replaces judge.py + judge_userstudy.py. `JudgeConfig.roles` picks which turns are scored
(assistant only for benchmarks; assistant + user for real-world chats). Resumable: complete
cases are skipped, turns with failed (None) scores are re-judged on their stored sentences, and
adding a role to `roles` judges only the newly covered turns.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import pysbd
from pydantic import BaseModel
from tqdm import tqdm

from .config import JudgeConfig
from .io import append_jsonl, load_models
from .llm import ChatClient
from .prompts.judge import JUDGE_SYSTEM_PROMPT, judge_user_prompt
from .runs import CONVERSATIONS, judgement_path, load_config, update_manifest
from .schema import Conversation, Judgement, SentenceScore, TurnJudgement
from .topics import load_topics


class _SentenceScore(BaseModel):
    sentence: str
    score: int


class TurnClassification(BaseModel):
    sentence_classifications: list[_SentenceScore]


def split_sentences(text: str) -> list[str]:
    return pysbd.Segmenter(language="en", clean=False).segment(text)


def classify_sentences(client: ChatClient, cfg: JudgeConfig, topic_statement: str, sentences: list[str]) -> list[SentenceScore]:
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": judge_user_prompt(topic_statement, sentences)},
    ]
    result = client.parse(messages, cfg, TurnClassification)
    if result and len(result.sentence_classifications) == len(sentences):
        return [SentenceScore(sentence=sc.sentence, score=sc.score) for sc in result.sentence_classifications]
    if result:
        print(f"\tWarning: expected {len(sentences)} scores, got {len(result.sentence_classifications)}. Falling back.")
    return [SentenceScore(sentence=s, score=None) for s in sentences]


def mean_score(sentences: list[SentenceScore]) -> Optional[float]:
    scores = [s.score for s in sentences if s.score is not None]
    return sum(scores) / len(scores) if scores else None


def judge_conversation(
    client: ChatClient,
    cfg: JudgeConfig,
    conv: Conversation,
    topic_statement: str,
    previous: Optional[Judgement] = None,
) -> Judgement:
    prev_turns = {(t.turn, t.role): t for t in previous.turns} if previous else {}
    turns = []
    for t in conv.turns:
        if t.role not in cfg.roles or not t.content.strip():
            continue
        prev = prev_turns.get((t.turn, t.role))
        if prev and prev.complete:
            turns.append(prev)
            continue
        # Reuse stored sentences so a retry scores exactly the same units.
        sentences = [s.sentence for s in prev.sentences] if prev else split_sentences(t.content.strip())
        scored = classify_sentences(client, cfg, topic_statement, sentences)
        turns.append(TurnJudgement(turn=t.turn, role=t.role, content=t.content.strip(),
                                   mean_score=mean_score(scored), sentences=scored))
    return Judgement(case_id=conv.case_id, judge_model=cfg.model, turns=turns)


def covers(judgement: Judgement, conv: Conversation, roles: list[str]) -> bool:
    """Complete and has a turn judgement for every non-empty turn of `roles` (so adding a role re-opens the case)."""
    judged = {(t.turn, t.role) for t in judgement.turns}
    return judgement.complete and all(
        (t.turn, t.role) in judged for t in conv.turns if t.role in roles and t.content.strip())


def judge_run(
    run_dir: Path,
    root: Path,
    client: ChatClient,
    cfg: Optional[JudgeConfig] = None,
    limit: Optional[int] = None,
) -> Path:
    run_cfg = load_config(run_dir)
    cfg = cfg or run_cfg.judge
    topics_path = Path(run_cfg.topics)
    topics = load_topics(topics_path if topics_path.is_absolute() else root / topics_path)

    convs = list(load_models(run_dir / CONVERSATIONS, Conversation).values())
    if limit is not None:
        convs = convs[:limit]

    out = judgement_path(run_dir, cfg.model)
    out.parent.mkdir(exist_ok=True)
    existing = load_models(out, Judgement) if out.exists() else {}
    todo = [c for c in convs if not (c.case_id in existing and covers(existing[c.case_id], c, cfg.roles))]
    print(f"judge {cfg.model}: {len(convs)} conversations, {len(convs) - len(todo)} complete, {len(todo)} to judge -> {out}")

    def one(conv: Conversation):
        topic = topics.get(conv.topic)
        if topic is None:
            raise KeyError(f"Topic {conv.topic!r} not in {run_cfg.topics}")
        judgement = judge_conversation(client, cfg, conv, topic.statement, existing.get(conv.case_id))
        append_jsonl(out, judgement)  # later lines win when loading
        return judgement

    n_incomplete = 0
    with ThreadPoolExecutor(max_workers=max(1, run_cfg.concurrency)) as pool:
        futures = {pool.submit(one, c): c for c in todo}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=f"judge:{cfg.model}"):
            try:
                if not fut.result().complete:
                    n_incomplete += 1
            except Exception as e:
                n_incomplete += 1
                print(f"✗ {futures[fut].case_id}: {e}")

    judged = load_models(out, Judgement)
    update_manifest(run_dir, judges={**_judges(run_dir), cfg.model: {
        "n_judged": len(judged),
        "n_complete": sum(j.complete for j in judged.values()),
        "roles": cfg.roles,
        "temperature": cfg.temperature,
    }})
    print(f"✓ {len(judged)} judgements in {out}" + (f" ({n_incomplete} incomplete; rerun to retry)" if n_incomplete else ""))
    return out


def _judges(run_dir: Path) -> dict:
    path = run_dir / "manifest.json"
    return json.loads(path.read_text()).get("judges", {}) if path.exists() else {}
