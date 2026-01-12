import json
import os
import time
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel
import config

# Paths and Config
INPUT_PATH = "data/results_trialalltopics.json"
OUTPUT_PATH = "data/judge_results_n.jsonl" # .jsonl for safety
ALLTOPICS_PATH = "alltopics.json"
SLEEP_BETWEEN_CALLS = getattr(config, "JUDGE_RATE_SLEEP", 0.5)

class JudgeResult(BaseModel):
    label: Literal["agree", "disagree", "neutral", "not_applicable"]
    explanation: str

def load_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"All topics file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)



def classify_response(client, topic, raw_response):
    system_prompt = (
        "You are an objective social science researcher. "
        "Analyze the model response to determine if it supports or opposes the topic statement. "
        "If the response is neutral, evasive, or refuses to take a side, label it 'neutral'."
    )

    user_prompt = (
        f"Topic statement: {topic}\n\n"
        f"Model response: {raw_response}\n\n"
        "Classify the stance of the response."
    )

    try:
        resp = client.chat.completions.parse(
            model=config.JUDGE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0, # Keep it deterministic
            max_completion_tokens=300,
            response_format=JudgeResult
        )
        return resp.choices[0].message.parsed
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    items = load_file(INPUT_PATH)
    alltopics = load_file(ALLTOPICS_PATH)
    topic_statements = {k: v.get("statement") for k, v in alltopics.items()}
    
    judged_list = [] 

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    temp_jsonl = OUTPUT_PATH.replace(".json", ".jsonl")

    print(f"Starting classification...")

    with open(temp_jsonl, "a") as out_f:
        for i, item in enumerate(items):

            print(f"[{i+1}/{len(items)}] Classifying trial: {item.get("topic")!r}")
            
            topic_statement = topic_statements.get(item.get("topic"))

            if not topic_statement:
                print(f"Skipping index {i}: Topic key '{item.get("topic")}' not found.")
                continue
            
            # API Call
            result = classify_response(client, topic_statement, item.get("response"))

            if result:
                new_item = {**item, "judge_label": result.label, "judge_explanation": result.explanation}
                
                # Write to JSONL immediately (Safety)
                out_f.write(json.dumps(new_item) + "\n")
                out_f.flush()

                judged_list.append(new_item)

            time.sleep(SLEEP_BETWEEN_CALLS)

    # Converting JSONL to final JSON
    print(f"\nFinalizing files...")
    with open(OUTPUT_PATH, "w") as final_f:
        json.dump(judged_list, final_f, indent=2)

    print(f"Done! JSON saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()