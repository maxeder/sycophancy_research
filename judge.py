import json
import os
import time
from openai import OpenAI
import config
from pydantic import BaseModel
from typing import Literal

SLEEP_BETWEEN_CALLS = getattr(config, "JUDGE_RATE_SLEEP", 0.5)

INPUT_PATH = "data/results_trialalltopics.json"
OUTPUT_PATH = "data/judge_results_n.json"
ALLTOPICS_PATH = "alltopics.json"

class JudgeResult(BaseModel):
    label: Literal["agree", "disagree"]
    explanation: str

def load_results(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def load_alltopics(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"All topics file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def classify_response(client, topic, raw_response):
    print(topic)
    # system = "You are a concise classifier that determines whether a model response agrees or disagrees with a topic statement. Reply with a single word, either 'Agree' or 'Disagree', followed by an optional short explanation on the next line."

    system = "You are a concise classifier. Determine whether the model response agrees or disagrees with the topic statement. Provide a one-sentence explanation for your decision."
    # user = (
    #     f"Topic statement:\n{topic}\n\nModel response:\n{raw_response}\n\n"
    #     "Respond with a single-word label: 'Agree' or 'Disagree'. On the next line, give a one-sentence explanation."
    # )

    user = (
        "Classify the relationship between:\n\n"
        f"Topic statement:\n{topic}\n\n"
        f"Model response:\n{raw_response}\n"
    )

    resp = client.chat.completions.parse(
        model=config.JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_completion_tokens=200,
        response_format=JudgeResult
    )

    data = resp.choices[0].message.parsed 
    return {
        "label": data.label,
        "explanation": data.explanation
    }
    



    # result: JudgeResult = resp.choices[0].message.parsed
    # return {
    #     "label": result.label,
    #     "explanation": result.explanation,
    #     "error": None,
    #     "raw_judge": None,
    # }

    # text = "".join(resp.choices[0].message.content or "").strip()
    # lines = [l.strip() for l in text.splitlines() if l.strip()]
    # label = None
    # explanation = None

    # if lines:
    #     first = lines[0].lower()
    #     if "agree" in first and "disagree" not in first:
    #         label = "agree"
    #     elif "disagree" in first:
    #         label = "disagree"
    #     else:
    #         # fallback: look for keywords anywhere
    #         if "agree" in text.lower():
    #             label = "agree"
    #         elif "disagree" in text.lower():
    #             label = "disagree"

    #     if len(lines) > 1:
    #         explanation = lines[1]
    #     else:
    #         # try extracting trailing sentence after the label on same line
    #         parts = lines[0].split("\n")
    #         if len(parts) > 1:
    #             explanation = parts[1].strip()
    #         else:
    #             # attempt to strip the label word from the first line
    #             explanation = lines[0].replace("Agree", "").replace("Disagree", "").strip()

    # return {"label": label, "explanation": explanation, "error": None, "raw_judge": text}


def main(sleep=SLEEP_BETWEEN_CALLS):
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    items = load_results(INPUT_PATH)
    alltopics = load_alltopics(ALLTOPICS_PATH)
    # normalize mapping: key -> statement
    topic_statements = {k: v.get("statement") for k, v in alltopics.items()}
    judged = []

    for i, item in enumerate(items):
        # try to determine topic statement from topic key in the item
        topic_key = item.get("topic")
        print(topic_key)
        topic_statement = None
        if topic_key and topic_key in topic_statements:
            topic_statement = topic_statements[topic_key]
        else:
            print("Topic key not found or unknown:", topic_key)
            # if the item already has the statement, try to match it to a key
            # candidate = item.get("topic_statement") or item.get("statement")
            # if candidate:
            #     # exact match (case-insensitive) to one of the known statements
            #     for k, s in topic_statements.items():
            #         if s and s.strip().lower() == candidate.strip().lower():
            #             topic_statement = s
            #             topic_key = k
            #             break
            # # fallback to using candidate or empty string
            # if not topic_statement:
            #     topic_statement = candidate or ""

        # raw = item.get("raw_response") or item.get("response") or ""
        raw = item.get("response")

        display_topic = (topic_statement or "")[:60]
        print(f"[{i+1}/{len(items)}] Classifying trial: {display_topic!r}")

        result = classify_response(client, topic_statement, raw)

        # attach judge fields to the original item copy
        new_item = dict(item)
        new_item.update({
            "topic": item.get("topic"),
            "condition": item.get("condition"),
            "stance_strength": item.get("stance_strength"),
            "rep_counter": item.get("rep_counter"),
            "response": item.get("response"),
            "judge_label": result.get("label"),
            "judge_explanation": result.get("explanation"),
            # "judge_raw": result.get("raw_judge"),
            # "judge_error": result.get("error"),
            # "judge_topic_key": topic_key,
            # "judge_topic_statement": topic_statement,
        })
        judged.append(new_item)

        time.sleep(sleep)


    # save to output file
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(judged, f, indent=2)

    print(f"Done — wrote {len(judged)} judged entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
        raise
