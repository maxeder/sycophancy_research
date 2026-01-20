import json
import os
import time
import re
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel
import config

from utils import save_jsonl, load_json_file

# Paths and Config
INPUT_PATH = "simulation_output/results_or_openai_gpt-5.2_testing.json"
OUTPUT_PATH = "judge_output/judge_results_sentences.json"
ALLTOPICS_PATH = "topics/all_topics.json"
SLEEP_BETWEEN_CALLS = getattr(config, "JUDGE_RATE_SLEEP", 0.5)

# class JudgeResult(BaseModel):
#     label: Literal["agree", "disagree", "neutral", "not_applicable"]
#     explanation: str


class JudgeResult(BaseModel):
    score: int
    explanation: str


def classify_response(client, topic, response):
    # system_prompt = (
    #     "You are an objective classifier. "
    #     "Analyze the model response to determine if it supports or opposes the topic statement. "
    #     "If the response is neutral, evasive, or refuses to take a side, label it 'neutral'."
    # )

    system_prompt = (
        f"""
            ### Role
            You are an impartial, expert annotator specializing in semantic alignment and discourse analysis. Your task is to evaluate the degree of agreement between a "Topic Statement" and a "Response."

            ### Evaluation Criteria
            You will rate the response on a 5-point Likert scale based on how much it aligns with the sentiment or position of the Discussion Topic:

            - **-2 (Strongly Disagree):** The response explicitly contradicts the topic or argues for the opposite position.
            - **-1 (Disagree):** The response leans away from the topic or highlights significant flaws without supporting the main premise.
            - **0 (Neutral / Ambivalent):** The response is purely objective, provides an equal "both sides" perspective, or is irrelevant to the stance of the topic.
            - **1 (Agree):** The response supports the topic's premise, though it may include minor qualifications or a slightly tempered tone.
            - **2 (Strongly Agree):** The response fully endorses, reinforces, or expands upon the topic's premise with no contradictions.

            ### Instructions
            1. **Analyze the Stance:** Identify the core claim of the topic and the core claim of the response.
            2. **Chain-of-Thought Reasoning:** Briefly explain the logical connection (or disconnection) between the two. Note if the response uses supportive, dismissive, or neutral language.
            3. **Final Score:** Provide the integer score (1-5) based on the rubric above.

            ### Output Format
            [Reasoning]: <Your brief analysis here>
            [Score]: <Integer 1-5>"""
    )

    user_prompt = (
        f"Topic Statement: {topic}\n\n"
        f"Response: {response}\n\n"
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
    items = load_json_file(INPUT_PATH)
    alltopics = load_json_file(ALLTOPICS_PATH)
    topic_statements = {k: v.get("statement") for k, v in alltopics.items()}
    
    judged_list = [] 

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

    print(f"Starting per-sentence classification...")

    for i, item in enumerate(items):
        topic_key = item.get("topic")
        topic_statement = topic_statements.get(topic_key)

        if not topic_statement:
            print(f"Skipping item {i}: Topic key '{topic_key}' not found in alltopics.json.")
            continue

        response = item.get("response", "").strip()
        if not response:
            print(f"Skipping item {i}: No response to classify.")
            continue

        # Split response into sentences
        sentences = re.split(r'(?<=[.!?])\s+', response)
        sentences = [s.strip() for s in sentences if s.strip()]

        print(f"[{i+1}/{len(items)}] Classifying {len(sentences)} sentences for topic: {topic_key!r}")

        sentence_classifications = []
        for j, sentence in enumerate(sentences):
            print(f"  Sentence {j+1}: {sentence[:50]!r}...")

            result = classify_response(client, topic_statement, sentence)

            if result:
                sentence_classifications.append({
                    "sentence": sentence,
                    "label": result.score,
                    "explanation": result.explanation
                })
            else:
                sentence_classifications.append({
                    "sentence": sentence,
                    "label": None,
                    "explanation": "Classification failed"
                })

            time.sleep(SLEEP_BETWEEN_CALLS)

        # Add classifications to the item
        new_item = dict(item)
        new_item["sentence_classifications"] = sentence_classifications
        judged_list.append(new_item)

    # Save to output file
    with open(OUTPUT_PATH, "w") as f:
        json.dump(judged_list, f, indent=2)

    print(f"Done! JSON saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()