import json
import os
import random
import time
from openai import OpenAI
from datetime import datetime
import config
import prompts
import argparse
from utils import save_jsonl, load_json_file, convert_jsonl_to_json

# no baseline atm

# openRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.OPENROUTER_API_KEY
    )

# --testing to run a single trial for quick checks
parser = argparse.ArgumentParser()
parser.add_argument('--testing', action='store_true', help='Run in testing mode (single iteration)')
args = parser.parse_args()

TESTING = args.testing

print("Testing: " + str(TESTING))

OUTPUT_PATH = 'simulation_output/results_multiturn_' + config.TARGET_PROVIDER.lower().replace('/', '_') + config.TARGET_MODEL.lower() + ('.jsonl' if not TESTING else '_testing.jsonl')
TOPICS_FILE = 'topics/all_topics.json'
# ! use json file (not jsonl) for loading synthetic user data
INPUT_FILE = 'userdata_output/data_openai_gpt-5.2_testing.json'

class QueryModelError(Exception):
    pass


def query_model(messages):
    """Query model with conversation history."""

    try:
        response = client.chat.completions.create(
            model=config.TARGET_PROVIDER + config.TARGET_MODEL,
            messages=messages,
            max_tokens=config.TARGET_MAX_TOKENS,
            temperature=config.TARGET_TEMPERATURE
        )
    except Exception as e:
        raise QueryModelError(f"API call failed: {e}") from e

    if not getattr(response, "choices", None):
        raise QueryModelError(f"No choices in response: {response!r}")

    choice = response.choices[0]
    msg = getattr(choice, "message", None)
    if msg is None or not getattr(msg, "content", None):
        raise QueryModelError(f"Empty message content in response: {response!r}")

    return msg.content


def run_single_trial(user_prompts, system_prompt=prompts.TARGET_SYSTEM_PROMPT):
    """Run one experimental trial with full conversation history."""
    
    # Initialize conversation history with system prompt
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Query model with one user prompt at a time, maintaining history
    for prompt in user_prompts:
        # Add user message to history
        messages.append({"role": "user", "content": prompt["user_prompt"]})
        
        response = query_model(messages)
        messages.append({"role": "assistant", "content": response})
        
    return {
        'transcript': messages
    }



def run_experiment():
    """Run full experiment."""

    # Load generated user data
    syn_user_data = load_json_file(INPUT_FILE)

    print("Loaded synthetic user data: ", syn_user_data)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Initialize or clear the output file
    with open(OUTPUT_PATH, 'w') as f:
        pass  # Create/clear the file
    try:
        for case in (syn_user_data[:1] if TESTING else syn_user_data):
            case_id = case['case_id']
            topic_key = case['topic_key']
            topic_question = case['topic_question']
            target_stance = case['target_stance']
            framing = case['framing']
            rep_counter = case['rep_counter']

            print(f"Getting responses for: {topic_key} | {target_stance} | {framing} | Rep {rep_counter}")
            transcript = run_single_trial(case['turns'])

            result = {
                "case_id": case_id,
                "topic_key": topic_key,
                "topic_question": topic_question,
                "target_stance": target_stance,  
                "framing": framing,
                "rep_counter": rep_counter,       
                "transcript": transcript
            }

            if transcript:
                save_jsonl(result, OUTPUT_PATH)
        
                print(f"✓ Saved results")
            else:
                print(f"✗ No result returned")
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        convert_jsonl_to_json(OUTPUT_PATH)

    print(f"Simulation complete! Saved to '{OUTPUT_PATH}'.")
    return


if __name__ == "__main__":
    run_experiment()