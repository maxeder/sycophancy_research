"""Adapter for the user-study chats (user-study/analysis/all_chats.json, built by combine_chats.py)."""

from pathlib import Path
from typing import Iterator

from ...io import read_records
from ...schema import Conversation, make_case_id
from .base import number_turns, register

PLATFORM_MODEL = "openai/gpt-5.2"  # model behind user-study/platform/functions/index.js


def chat_to_conversation(chat: dict) -> Conversation:
    return Conversation(
        case_id=make_case_id("real_world", "user_study", chat["case"]),
        approach="real_world",
        topic=chat["topic"],
        condition=chat["condition"],
        target_model=PLATFORM_MODEL,
        turns=number_turns(chat["transcript"]),
        meta={
            "source": "user_study",
            "participant": chat["case"],  # internal study number, not the Prolific ID
            "pre_opinion": chat.get("pre_opinion"),
            "post_opinion": chat.get("post_opinion"),
        },
    )


@register("user_study")
def load_user_study(path: Path) -> Iterator[Conversation]:
    for chat in read_records(path):
        yield chat_to_conversation(chat)
