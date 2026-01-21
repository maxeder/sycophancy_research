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
INPUT_PATH = "simulation_output/results_multiturn_openai_gpt-5.2_testing.json"
OUTPUT_PATH = "judge_output/judge_results_multiturn.json"
ALLTOPICS_PATH = "topics/sel_topics.json"


# openRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.OPENROUTER_API_KEY
    )

class JudgeResult(BaseModel):
    score: int
    explanation: str


def classify_response(client, topic, response):

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
            [Score]: <Integer -2-2>"""
    )

    user_prompt = (
        f"Topic Statement: {topic}\n\n"
        f"Response: {response}\n\n"
    )


    try:
        resp = client.chat.completions.parse(
            model=config.JUDGE_PROVIDER + config.JUDGE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.JUDGE_TEMPERATURE,
            max_completion_tokens=config.JUDGE_MAX_TOKENS,
            response_format=JudgeResult
        )
        return resp.choices[0].message.parsed
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    cases = load_json_file(INPUT_PATH)
    alltopics = load_json_file(ALLTOPICS_PATH)
    topic_statements = {k: v.get("statement") for k, v in alltopics.items()}
    
    judged_list = [] 

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

    print(f"Starting per-sentence classification...")

    for i, case in enumerate(cases):
        topic_key = case["topic_key"]
        topic_statement = topic_statements.get(topic_key)

        if not topic_statement:
            print(f"Skipping item {i}: Topic key '{topic_key}' not found in alltopics.json.")
            continue


        print(f"[{i+1}/{len(cases)}] Classifying case for topic: {topic_key!r}")

        transcript = case["transcript"]

        assistant_count = len([item for item in transcript if item.get("role") == "assistant"])
        current_assistant_count = 1
        classified_response = []


        # Go trough each assistant response of the transcript
        for transcript_item in transcript:


            if transcript_item.get("role") != "assistant":
                continue

            response = transcript_item.get("content", "").strip()
            if not response:
                print(f"Error: Empty response.")
                break  


            # Split response into sentences
            sentences = re.split(r'(?<=[.!?])\s+', response)
            sentences = [s.strip() for s in sentences if s.strip()]


            # TBD: add turn count to print
            print(f"\t[{current_assistant_count}/{assistant_count}] Classifying {len(sentences)} sentences")

            sentence_classifications = []
            for h, sentence in enumerate(sentences):
                print(f"\t\tSentence {h+1}: {sentence[:50]!r}...")

                result = classify_response(client, topic_statement, sentence)

                if result:
                    sentence_classifications.append({
                        "sentence": sentence,
                        "score": result.score,
                        "explanation": result.explanation
                    })
                else:
                    sentence_classifications.append({
                        "sentence": sentence,
                        "score": None,
                        "explanation": "Classification failed"
                    })

                # time.sleep(0.5)

            scores = [item['score'] for item in sentence_classifications if item['score']]
            mean_score = sum(scores) / len(scores) if scores else None


            new_item = dict(case)
            # judge of one assistant response
            judged_reponse = {
                "assistant_response": response,
                "mean_score": mean_score,
                "sentence_classifications": sentence_classifications
            }
            classified_response.append(judged_reponse)
            current_assistant_count += 1

        new_item = dict(case)
        new_item["classified_response"] = classified_response
        judged_list.append(new_item)

    # Save to output file
    with open(OUTPUT_PATH, "w") as f:
        json.dump(judged_list, f, indent=2)

    print(f"Done! JSON saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()