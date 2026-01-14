import json
import os
import random
import time
from openai import OpenAI
from datetime import datetime
import config
import prompts

# openAI client
# client = OpenAI(api_key=config.OPENAI_API_KEY)

# openRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.OPENROUTER_API_KEY
    )

# Only one topic / condition / replication for testing purposes
TESTING = True


OUTPUT_PATH = 'simulation_output/results_or_' + config.PROVIDER.lower().replace('/', '_') + config.MODEL.lower() + ('.json' if not TESTING else '_testing.json')
TOPICS_FILE = 'topics/all_topics.json'

def load_topics():
    """Load topics from JSON file."""
    with open(TOPICS_FILE, 'r') as f:
        return json.load(f)
    

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



# def parse_response(response_text):
#     """Extract position and reasoning from response."""
#     lines = response_text.split('\n')
#     position = None
#     reasoning = None
    
#     for line in lines:
#         if line.startswith('Position:'):
#             position = line.split('Position:')[1].strip().lower()
#             if 'agree' in position and 'disagree' not in position:
#                 position = 'agree'
#             elif 'disagree' in position:
#                 position = 'disagree'
#         elif line.startswith('Reasoning:'):
#             reasoning = line.split('Reasoning:')[1].strip()
    
#     return {
#         'position': position,
#         'reasoning': reasoning,
#         'raw_response': response_text
#     }

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
    
    # parsed = parse_response(response)
    
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
    topics_data = load_topics()
    results = []
    
    total_trials = len(topics_data) * len(config.CONDITIONS) * config.N_REPLICATIONS
    
    trial_count = 0
    try:
        # limit to first 1 topic for testin
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
                        results.append(result)
                    else:
                        raise RuntimeError("Error in trial execution")
                    
                    # Rate limit
                    time.sleep(0.5)

    except Exception as e:
        print("Script stopped:", e)
        exit(1)  
    
    # Save results
    # os.makedirs('data', exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nExperiment complete! {len(results)} trials saved.")
    return results

if __name__ == "__main__":
    run_experiment()