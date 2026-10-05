"""Convert the frozen thesis outputs in legacy/ into standard run directories.

`syco import-legacy` creates runs/legacy_multi_turn_thesis and runs/legacy_user_study, so the
thesis data flows through the same export as new runs, and new runs can be compared with it
case by case (case ids match).
"""

from pathlib import Path

from .approaches.real_world.user_study import chat_to_conversation
from .config import JudgeConfig, ModelConfig, RunConfig
from .io import read_records, write_jsonl
from .runs import CONVERSATIONS, judgement_path, update_manifest, write_config
from .schema import (Conversation, Judgement, SentenceScore, Turn, TurnJudgement, make_case_id,
                     stance_from_label)

LEGACY_CONDITIONS = ("unprompted", "sycophantic", "contrarian")
LEGACY_TARGET = ModelConfig(model="openai/gpt-5.2", temperature=0.0, max_tokens=1500)
LEGACY_JUDGE = JudgeConfig(model="google/gemini-2.5-flash", temperature=0.0, max_tokens=3500)


def multi_turn_case_id(record: dict, condition: str) -> str:
    return make_case_id("multi_turn", record["topic_key"], stance_from_label(record["user_stance"]),
                        condition, record["attribution"], record["rep_counter"])


def conversation_from_legacy_multi_turn(record: dict, condition: str) -> Conversation:
    return Conversation(
        case_id=multi_turn_case_id(record, condition),
        approach="multi_turn",
        topic=record["topic_key"],
        topic_question=record.get("topic_question"),
        user_stance=stance_from_label(record["user_stance"]),
        condition=condition,
        attribution=record["attribution"],
        rep=record["rep_counter"],
        target_model=LEGACY_TARGET.model,
        turns=[Turn(role=t["role"], content=t["content"], turn=t.get("turn")) for t in record["transcript"]],
        meta={"script_id": record["case_id"]},
    )


def _sentences(items: list[dict]) -> list[SentenceScore]:
    return [SentenceScore(sentence=s["sentence"], score=s["score"]) for s in items]


def judgement_from_legacy_multi_turn(record: dict, condition: str) -> Judgement:
    return Judgement(
        case_id=multi_turn_case_id(record, condition),
        judge_model=LEGACY_JUDGE.model,
        turns=[TurnJudgement(turn=t["turn"], role="assistant", content=t["assistant_response"],
                             mean_score=t["mean_score"], sentences=_sentences(t["sentence_classifications"]))
               for t in record["classified_response"]],
    )


def judgement_from_legacy_user_study(record: dict) -> Judgement:
    conv = chat_to_conversation(record)
    return Judgement(
        case_id=conv.case_id,
        judge_model=LEGACY_JUDGE.model,
        turns=[TurnJudgement(turn=t["turn"], role=t["role"], content=t["content"],
                             mean_score=t["mean_score"], sentences=_sentences(t["sentence_classifications"]))
               for t in record["classified_response"]],
    )


def _write_run(run_dir: Path, cfg: RunConfig, convs: list[Conversation], judgements: list[Judgement], sources: list[str]):
    run_dir.mkdir(parents=True, exist_ok=True)
    write_config(run_dir, cfg)
    write_jsonl(run_dir / CONVERSATIONS, convs)
    write_jsonl(judgement_path(run_dir, LEGACY_JUDGE.model), judgements)
    update_manifest(run_dir, legacy=True, sources=sources, name=cfg.name, approach=cfg.approach,
                    target_model=cfg.target.model if cfg.target else convs[0].target_model,
                    n_cases=len(convs), n_done=len(convs),
                    judges={LEGACY_JUDGE.model: {"n_judged": len(judgements),
                                                 "n_complete": sum(j.complete for j in judgements),
                                                 "roles": cfg.judge.roles}})
    print(f"✓ {run_dir}: {len(convs)} conversations, {len(judgements)} judgements")


def import_legacy(root: Path) -> list[Path]:
    legacy = root / "legacy"
    runs = []

    convs, judgements, sources = [], [], []
    for condition in LEGACY_CONDITIONS:
        sim = legacy / "simulation_output" / f"{condition}_results_multiturn_openai_gpt-5.2.json"
        judged = legacy / "judge_output" / f"{condition}_judge_results_multiturn_gemini-2.5-flash.json"
        convs += [conversation_from_legacy_multi_turn(r, condition) for r in read_records(sim)]
        judgements += [judgement_from_legacy_multi_turn(r, condition) for r in read_records(judged)]
        sources += [str(sim.relative_to(root)), str(judged.relative_to(root))]
    cfg = RunConfig(name="legacy_multi_turn_thesis", approach="multi_turn", conditions=list(LEGACY_CONDITIONS),
                    target=LEGACY_TARGET, judge=LEGACY_JUDGE,
                    params={"scripts": "data/scripts/new_data_8_turns_openai_gpt-5.2.json"})
    run_dir = root / "runs" / "legacy_multi_turn_thesis"
    _write_run(run_dir, cfg, convs, judgements, sources)
    runs.append(run_dir)

    judged = legacy / "user_study" / "user_study_judged.json"
    records = read_records(judged)
    cfg = RunConfig(name="legacy_user_study", approach="real_world", conditions=list(LEGACY_CONDITIONS),
                    judge=JudgeConfig(**{**LEGACY_JUDGE.model_dump(), "roles": ["assistant", "user"]}),
                    params={"adapter": "user_study", "source": "../user-study/analysis/all_chats.json"})
    run_dir = root / "runs" / "legacy_user_study"
    _write_run(run_dir, cfg, [chat_to_conversation(r) for r in records],
               [judgement_from_legacy_user_study(r) for r in records], [str(judged.relative_to(root))])
    runs.append(run_dir)
    return runs
