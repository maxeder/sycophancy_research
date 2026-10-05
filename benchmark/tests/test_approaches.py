import json

import pytest

from sycobench.approaches.multi_turn import generate_scripts
from sycobench.config import GenerateScriptsConfig, JudgeConfig, ModelConfig, RunConfig
from sycobench.io import load_models, read_records
from sycobench.prompts.target_system import target_system_prompt
from sycobench.prompts.user_sim import PERSUASION_TACTICS
from sycobench.runner import run
from sycobench.runs import CONVERSATIONS, ERRORS
from sycobench.schema import Conversation

TARGET = ModelConfig(model="test/target")


def convs(run_dir):
    return load_models(run_dir / CONVERSATIONS, Conversation)


def test_multi_turn_replays_script_under_each_condition(root, client):
    cfg = RunConfig(name="mt", approach="multi_turn", conditions=["unprompted", "contrarian"], target=TARGET,
                    params={"scripts": "data/scripts/small.json"})
    out = convs(run(cfg, root, client))

    assert sorted(out) == [
        "multi_turn:space:con:contrarian:self:0", "multi_turn:space:con:unprompted:self:0",
        "multi_turn:space:pro:contrarian:self:0", "multi_turn:space:pro:unprompted:self:0",
    ]
    conv = out["multi_turn:space:pro:contrarian:self:0"]
    script = json.loads((root / "data/scripts/small.json").read_text())[0]
    assert conv.turns[0].role == "system"
    assert conv.turns[0].content == target_system_prompt("contrarian", "space exploration as a worthwhile investment for humanity")
    assert [t.content for t in conv.turns if t.role == "user"] == [t["user_prompt"] for t in script["turns"]]
    assert [t.turn for t in conv.turns if t.role == "assistant"] == list(range(9))
    # target sees the full history each turn
    assert len(client.chat_calls[-1][1]) == 1 + 2 * 8 + 1


def test_single_turn_baseline_and_stances(root, client):
    cfg = RunConfig(name="st", approach="single_turn", topic_keys=["space"], conditions=["none"], target=TARGET,
                    params={"strengths": ["strong"], "n_reps": 2})
    out = convs(run(cfg, root, client))

    assert len(out) == 1 + 2 * 2  # 1 baseline + (pro, con) x 2 reps
    base = out["single_turn:space:-:none:-:0"]
    assert [t.role for t in base.turns] == ["user", "assistant"]  # condition "none" -> no system prompt
    assert base.turns[0].turn == 0
    pro = out["single_turn:space:pro:none:strong:1"]
    assert pro.turns[0].content.startswith("I'm absolutely convinced that space exploration")
    assert pro.turns[0].turn == 1


def test_simulated_user_alternates_models(root, client):
    cfg = RunConfig(name="sim", approach="simulated_user", topic_keys=["taxes"], conditions=["sycophantic"],
                    target=TARGET, params={"user_model": {"model": "test/user"}, "stances": ["con"]})
    conv = convs(run(cfg, root, client))["simulated_user:taxes:con:sycophantic:persuasion:0"]

    models = [m for m, _ in client.chat_calls]
    assert models == ["test/target"] + ["test/user", "test/target"] * len(PERSUASION_TACTICS)
    assert [t.turn for t in conv.turns if t.role == "user"] == list(range(len(PERSUASION_TACTICS) + 1))
    # the user model sees target replies as "user" messages
    _, user_view = client.chat_calls[3]
    assert [m["role"] for m in user_view] == ["system", "user", "assistant", "user"]
    assert 'You "disagree" with the statement' in user_view[0]["content"]


def test_real_world_numbers_turns_and_drops_unlisted_fields(root):
    cfg = RunConfig(name="rw", approach="real_world", conditions=["sycophantic", "contrarian"],
                    params={"adapter": "user_study", "source": "data/chats.json"})
    out = convs(run(cfg, root, client=None))

    conv = out["real_world:user_study:1"]
    assert [(t.role, t.turn) for t in conv.turns] == [
        ("system", None), ("assistant", 0), ("user", 1), ("assistant", 1), ("user", 2), ("assistant", 2)]
    assert conv.meta == {"source": "user_study", "participant": 1, "pre_opinion": 6, "post_opinion": 7}
    assert "SHOULD-NOT-LEAK" not in (root / "runs").joinpath(next((root / "runs").iterdir()).name, CONVERSATIONS).read_text()


def test_replay_keeps_greeting_and_regenerates_replies(root, client):
    cfg = RunConfig(name="rp", approach="replay", conditions=["sycophantic", "contrarian"], target=TARGET,
                    params={"adapter": "user_study", "source": "data/chats.json"})
    out = convs(run(cfg, root, client))

    assert list(out) == ["replay:real_world:user_study:1:sycophantic"]  # chat 2 has no user turns
    conv = out["replay:real_world:user_study:1:sycophantic"]
    assert [(t.role, t.turn) for t in conv.turns][1:] == [("assistant", 0), ("user", 1), ("assistant", 1), ("user", 2), ("assistant", 2)]
    assert conv.turns[1].content == "Hello! What do you think?"
    assert conv.turns[3].content.startswith("Reply 1 from test/target")
    assert conv.meta["source_case_id"] == "real_world:user_study:1"


def test_resume_skips_done_and_retries_errors(root):
    calls = {"n": 0}

    def flaky(messages, cfg):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom")
        return "ok."

    from tests.conftest import FakeClient
    cfg = RunConfig(name="st", approach="single_turn", topic_keys=["space"], conditions=["none"], target=TARGET,
                    params={"stances": ["pro"], "strengths": ["weak"], "n_reps": 3})
    run_dir = run(cfg, root, FakeClient(chat_fn=flaky))
    assert len(convs(run_dir)) == 2
    assert len(read_records(run_dir / ERRORS)) == 1

    retry = FakeClient()
    run(None, root, retry, resume=run_dir)
    assert len(convs(run_dir)) == 3
    assert len(retry.chat_calls) == 1


def test_new_run_refuses_to_overwrite(root, client):
    cfg = RunConfig(name="st", approach="single_turn", topic_keys=["space"], conditions=["none"], target=TARGET,
                    params={"stances": ["baseline"]})
    run(cfg, root, client)
    with pytest.raises(FileExistsError):
        run(cfg, root, client)


def test_generate_scripts_matches_thesis_format(root):
    from tests.conftest import FakeClient
    fake = FakeClient(chat_fn=lambda m, c: "```json\n" + json.dumps([f"msg {i}" for i in range(3)]) + "\n```")
    cfg = GenerateScriptsConfig(name="t", topic_keys=["space"], n_reps=1, n_turns=3)
    out = generate_scripts(cfg, root, fake)
    scripts = read_records(out)
    assert [s["case_id"] for s in scripts] == ["space_pro_self_rep0", "space_con_self_rep0"]
    assert scripts[0]["user_stance"] == "Pro"
    assert [t["turn_number"] for t in scripts[0]["turns"]] == [0, 1, 2, 3]

    # generated scripts feed straight into the multi-turn approach
    run_cfg = RunConfig(name="mt", approach="multi_turn", conditions=["unprompted"], target=TARGET,
                        params={"scripts": str(out)})
    assert len(convs(run(run_cfg, root, FakeClient()))) == 2


def test_unknown_condition_rejected():
    with pytest.raises(ValueError):
        RunConfig(name="x", approach="multi_turn", conditions=["flattering"], judge=JudgeConfig())
