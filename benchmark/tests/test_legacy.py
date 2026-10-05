"""The thesis outputs in legacy/ load into the new schema without loss."""

import json

import pytest

from sycobench.approaches.real_world.user_study import chat_to_conversation
from sycobench.legacy import (LEGACY_CONDITIONS, conversation_from_legacy_multi_turn,
                              judgement_from_legacy_multi_turn, judgement_from_legacy_user_study)
from tests.conftest import BENCHMARK

LEGACY = BENCHMARK / "legacy"


@pytest.mark.parametrize("condition", LEGACY_CONDITIONS)
def test_multi_turn_round_trip(condition):
    sim = json.loads((LEGACY / f"simulation_output/{condition}_results_multiturn_openai_gpt-5.2.json").read_text())
    judged = json.loads((LEGACY / f"judge_output/{condition}_judge_results_multiturn_gemini-2.5-flash.json").read_text())
    assert len(sim) == len(judged) == 200

    convs = [conversation_from_legacy_multi_turn(r, condition) for r in sim]
    judgements = [judgement_from_legacy_multi_turn(r, condition) for r in judged]
    assert len({c.case_id for c in convs}) == 200
    assert [c.case_id for c in convs] == [j.case_id for j in judgements]
    for rec, conv, j in zip(sim, convs, judgements):
        assert [t.content for t in conv.turns] == [t["content"] for t in rec["transcript"]]
        assert [t.content for t in conv.turns if t.role == "assistant"] == [t.content for t in j.turns]
        assert j.complete


def test_user_study_turns_match_turn_fix():
    """New adapter numbering equals the turn numbers turn_fix.py wrote into the judged file."""
    records = json.loads((LEGACY / "user_study/user_study_judged.json").read_text())
    assert len(records) == 115
    for rec in records:
        conv = chat_to_conversation(rec)
        j = judgement_from_legacy_user_study(rec)
        judged_turns = [(t.role, t.turn) for t in conv.turns if t.role != "system" and t.content.strip()]
        assert judged_turns == [(t.role, t.turn) for t in j.turns]
