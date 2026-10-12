import json
import re
import shutil
from pathlib import Path

import pytest

BENCHMARK = Path(__file__).resolve().parents[1]


class FakeClient:
    """Deterministic stand-in for OpenRouterClient. Records every call."""

    def __init__(self, score: int = 1, fail_parse: int = 0, chat_fn=None):
        self.score = score
        self.fail_parse = fail_parse  # number of parse calls that return None before succeeding
        self.chat_fn = chat_fn
        self.chat_calls = []
        self.parse_calls = []

    def chat(self, messages, cfg):
        self.chat_calls.append((cfg.model, [dict(m) for m in messages]))
        if self.chat_fn:
            return self.chat_fn(messages, cfg)
        return f"Reply {len(self.chat_calls)} from {cfg.model}. It has two sentences."

    def parse(self, messages, cfg, response_format):
        self.parse_calls.append(messages)
        if self.fail_parse > 0:
            self.fail_parse -= 1
            return None
        sentences = re.findall(r"^\d+\. (.*)$", messages[1]["content"], re.M)
        return response_format(sentence_classifications=[{"sentence": s, "score": self.score} for s in sentences])


@pytest.fixture
def root(tmp_path) -> Path:
    """A throwaway project root with the real topics and a 2-script subset of the thesis scripts."""
    shutil.copytree(BENCHMARK / "data" / "topics", tmp_path / "data" / "topics")
    scripts = json.loads((BENCHMARK / "data/scripts/new_data_8_turns_openai_gpt-5.2.json").read_text())
    (tmp_path / "data" / "scripts").mkdir()
    (tmp_path / "data/scripts/small.json").write_text(json.dumps([scripts[0], scripts[20]]))
    chats = [
        {"case_id": "1-space-sycophantic", "case": 1, "condition": "sycophantic", "topic": "space",
         "pre_opinion": 6, "post_opinion": 7, "prolific_id": "SHOULD-NOT-LEAK",
         "transcript": [
             {"role": "system", "content": "sys"},
             {"role": "assistant", "content": "Hello! What do you think?"},
             {"role": "user", "content": "I love space."},
             {"role": "assistant", "content": "Great point."},
             {"role": "user", "content": "Mars next."},
             {"role": "assistant", "content": "Absolutely."},
         ]},
        {"case_id": "2-quota-contrarian", "case": 2, "condition": "contrarian", "topic": "quota",
         "pre_opinion": 2, "post_opinion": 2,
         "transcript": [{"role": "system", "content": "sys"}, {"role": "assistant", "content": "Hello!"}]},
    ]
    (tmp_path / "data/chats.json").write_text(json.dumps(chats))
    (tmp_path / "pyproject.toml").write_text("")
    return tmp_path


@pytest.fixture
def client():
    return FakeClient()
