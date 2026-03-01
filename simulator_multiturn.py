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
parser.add_argument('--unprompted', action='store_true', help='Set SYS_PROMPT_MODE to "unprompted"')
parser.add_argument('--syc', action='store_true', help='Set SYS_PROMPT_MODE to "sycophantic"')
parser.add_argument('--cont', action='store_true', help='Set SYS_PROMPT_MODE to "contrarian"')
args = parser.parse_args()

TESTING = args.testing

# Determine system prompt mode based on CLI flags
if args.syc:
    SYS_PROMPT_MODE = "sycophantic"
elif args.cont:
    SYS_PROMPT_MODE = "contrarian"
elif args.unprompted:
    SYS_PROMPT_MODE = "unprompted"
else:
    SYS_PROMPT_MODE = "unprompted"




print("Testing: " + str(TESTING))

OUTPUT_PATH = 'simulation_output/new_' + SYS_PROMPT_MODE + '_results_multiturn_' + config.TARGET_PROVIDER.lower().replace('/', '_') + config.TARGET_MODEL.lower() + ('.jsonl' if not TESTING else '_testing.jsonl')
TOPICS_FILE = 'topics/sel_topics.json'
# ! use json file (not jsonl) for loading synthetic user data
INPUT_FILE = 'userdata_output/new_data_8_turns_openai_gpt-5.2.json'

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


def run_single_trial(user_prompts, system_prompt):
    """Run one experimental trial with full conversation history."""
    
    # Initialize conversation history with system prompt
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Query model with one user prompt at a time, maintaining history
    for prompt in user_prompts:
        # Add user message to history
        messages.append({"role": "user", "turn": prompt["turn_number"], "content": prompt["user_prompt"]})
        
        response = query_model(messages)
        messages.append({"role": "assistant", "turn": prompt["turn_number"], "content": response})

        time.sleep(0.2)
        
    return {
        'transcript': messages
    }

def get_system_prompt(topic_key, topics_data):
    
    topic_about_phrase = topics_data.get(topic_key, {}).get("about_phrase", "the topic")

    if(SYS_PROMPT_MODE == "sycophantic"):
        system_prompt = prompts.SYCOPHANTIC_TARGET_SYSTEM_PROMPT.format(
            topic_about_phrase=topic_about_phrase
        )
    elif(SYS_PROMPT_MODE == "contrarian"):
        system_prompt = prompts.CONTRARIAN_TARGET_SYSTEM_PROMPT.format(
            topic_about_phrase=topic_about_phrase
        )
    else:  # unprompted
        system_prompt = prompts.DEFAULT_TARGET_SYSTEM_PROMPT.format(
            topic_about_phrase=topic_about_phrase
        )
    return system_prompt

def run_experiment():
    """Run full experiment."""

    # Load generated user data
    syn_user_data = load_json_file(INPUT_FILE)

    topics_data = load_json_file(TOPICS_FILE)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print(f"System prompt mode: {SYS_PROMPT_MODE}")
    
    # Initialize or clear the output file
    with open(OUTPUT_PATH, 'w') as f:
        pass  # Create/clear the file
    try:
        for case in (syn_user_data[:1] if TESTING else syn_user_data):
            case_id = case['case_id']
            topic_key = case['topic_key']
            topic_question = case['topic_question']
            user_stance = case['user_stance']
            attribution = case['attribution']
            rep_counter = case['rep_counter']

            print(f"Getting responses for: {topic_key} | {user_stance} | {attribution} | Rep {rep_counter}")

            system_prompt = get_system_prompt(topic_key, topics_data)

            # print(f"System Prompt: {system_prompt}")


            transcript = run_single_trial(case['turns'], system_prompt)

            result = {
                "case_id": case_id,
                "topic_key": topic_key,
                "topic_question": topic_question,
                "user_stance": user_stance,  
                "attribution": attribution,
                "rep_counter": rep_counter,       
                "transcript": transcript["transcript"]
            }

            if transcript:
                save_jsonl(result, OUTPUT_PATH)
        
                print(f"✓ Saved results")
            else:
                print(f"✗ No result returned")
                break

            time.sleep(0.5)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        convert_jsonl_to_json(OUTPUT_PATH)

    print(f"Simulation complete! Saved to '{OUTPUT_PATH}'.")
    return


if __name__ == "__main__":
    run_experiment()