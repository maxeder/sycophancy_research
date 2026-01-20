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

# openAI client
# client = OpenAI(api_key=config.OPENAI_API_KEY)

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

print("testing: " + str(TESTING))

OUTPUT_PATH = 'simulation_output/results_or_' + config.PROVIDER.lower().replace('/', '_') + config.MODEL.lower() + ('.jsonl' if not TESTING else '_testing.jsonl')
TOPICS_FILE = 'topics/all_topics.json'


class QueryModelError(Exception):
    pass


def query_model(prompt, system_prompt=prompts.SYSTEM_PROMPT):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    print("messages:", messages)

    try:
        response = client.chat.completions.create(
            model=config.PROVIDER + config.MODEL,
            messages=messages,
            # max_completion_tokens=config.MAX_TOKENS,
            max_tokens=config.MAX_TOKENS,
            # temperature=config.TEMPERATURE,
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



def run_single_trial(topic, topic_statement, topic_strength, condition, stance_strength, replication_id):
    """Run one experimental trial."""
    
    prompt = prompts.create_prompt(
        topic_statement,
        condition,
        stance_strength
    )
    
    response = query_model(prompt)

    print("Response: " + response)

    if not response:
        return None
    
    return {
        'topic': topic,
        'topic_strength': topic_strength,
        'condition': condition,
        'stance_strength': stance_strength,
        'rep_counter': replication_id,
        'response': response
    }



def run_experiment():
    """Run full experiment."""
    topics_data = load_json_file()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Initialize or clear the output file
    with open(OUTPUT_PATH, 'w') as f:
        pass  # Create/clear the file
    
    total_trials = len(topics_data) * len(config.CONDITIONS) * config.N_REPLICATIONS
    
    trial_count = 0
    completed_trials = 0
    
    try:
        # limit to first 1 topic for testing
        topics_to_process = list(topics_data.items())
        if TESTING:
            topics_to_process = topics_to_process[:1]

        for topic, topic_content in topics_to_process:

            for condition in (config.CONDITIONS[:1] if TESTING else config.CONDITIONS):

                # For user stance conditions, vary strength over multiple replications; baseline only once 
                if condition == "baseline":
                    n_reps = 1
                else:
                    n_reps = config.N_REPLICATIONS

                
                for rep in range(1 if TESTING else n_reps):
                    trial_count += 1
                    print(f"Trial {trial_count}/{total_trials}: {topic_content['statement']} - {condition}")

                    if condition == "baseline":
                        stance_strength = None
                    else:
                        stance_strength = random.choice(config.STANCE_STRENGTHS)
                    
                    result = run_single_trial(topic, topic_content['statement'], topic_content['strength'], condition, stance_strength, rep)
                    if result:
                        save_jsonl(result, OUTPUT_PATH)
                        completed_trials += 1
                        print(f"✓ Saved result {completed_trials}")
                    else:
                        raise RuntimeError("Error in trial execution")
                    
                    # Rate limit
                    time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n\n⚠ Experiment interrupted by user!")
        print(f"Saved {completed_trials} trials to {OUTPUT_PATH}")
        if completed_trials > 0:
            convert_jsonl_to_json(OUTPUT_PATH)
        return completed_trials
    except Exception as e:
        print(f"\n\n⚠ Script stopped due to error: {e}")
        print(f"Saved {completed_trials} trials to {OUTPUT_PATH}")
        if completed_trials > 0:
            convert_jsonl_to_json(OUTPUT_PATH)
        return completed_trials
    
    print(f"\n✓ Experiment complete! {completed_trials} trials saved to {OUTPUT_PATH}")
    if completed_trials > 0:
        convert_jsonl_to_json(OUTPUT_PATH)
    return completed_trials

if __name__ == "__main__":
    run_experiment()