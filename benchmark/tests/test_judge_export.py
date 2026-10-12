import csv

from sycobench.config import ModelConfig, RunConfig
from sycobench.export import export
from sycobench.io import load_models
from sycobench.judge import judge_run
from sycobench.runner import run
from sycobench.runs import judgement_path
from sycobench.schema import Judgement
from tests.conftest import FakeClient

TARGET = ModelConfig(model="test/target")


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def make_run(root, client, **kw):
    cfg = RunConfig(name="mt", approach="multi_turn", conditions=["unprompted"], target=TARGET,
                    params={"scripts": "data/scripts/small.json"}, **kw)
    return run(cfg, root, client)


def test_judge_scores_assistant_turns_and_retries_failures(root, client):
    run_dir = make_run(root, client)
    judge = FakeClient(fail_parse=1)
    out = judge_run(run_dir, root, judge)

    judgements = load_models(out, Judgement)
    assert len(judgements) == 2
    assert sum(not j.complete for j in judgements.values()) == 1
    assert all(t.role == "assistant" for j in judgements.values() for t in j.turns)
    assert all(len(j.turns) == 9 for j in judgements.values())

    retry = FakeClient()
    judge_run(run_dir, root, retry)
    assert len(retry.parse_calls) == 1  # only the failed turn is re-judged
    assert all(j.complete for j in load_models(out, Judgement).values())


def test_judge_user_turns_for_real_world(root):
    cfg = RunConfig(name="rw", approach="real_world", conditions=["sycophantic"],
                    judge={"roles": ["assistant", "user"]},
                    params={"adapter": "user_study", "source": "data/chats.json"})
    run_dir = run(cfg, root, None)
    out = judge_run(run_dir, root, FakeClient())
    (j,) = load_models(out, Judgement).values()
    assert [(t.role, t.turn) for t in j.turns] == [("assistant", 0), ("user", 1), ("assistant", 1), ("user", 2), ("assistant", 2)]


def test_judge_model_override_writes_separate_file(root, client):
    run_dir = make_run(root, client)
    judge_run(run_dir, root, FakeClient())
    cfg = RunConfig(name="x", approach="multi_turn").judge.model_copy(update={"model": "other/judge"})
    judge_run(run_dir, root, FakeClient(score=-2), cfg)
    assert judgement_path(run_dir, "google/gemini-2.5-flash").exists()
    assert judgement_path(run_dir, "other/judge").exists()


def test_export_aligned_scores(root, client):
    run_dir = make_run(root, client)
    judge_run(run_dir, root, FakeClient(score=1))
    (out_dir,) = {p.parent for p in export([run_dir], root / "results")}

    turns = read_csv(out_dir / "turns.csv")
    assert len(turns) == 2 * 9
    con = [r for r in turns if r["user_stance"] == "con"]
    assert {r["aligned_score"] for r in con} == {"-1.0"}  # agreeing with the topic = disagreeing with a con user
    assert {r["delta_from_baseline"] for r in turns} == {"0.0"}
    assert turns[0]["meta_script_id"] == "space_pro_self_rep0"

    cases = read_csv(out_dir / "cases.csv")
    assert {r["flipped"] for r in cases} == {"False"}
    sentences = read_csv(out_dir / "sentences.csv")
    assert len(sentences) == 2 * 9 * 2  # fake replies have two sentences
