import json
import os
import random
import time
from openai import OpenAI
from datetime import datetime
import config
import prompts

client = OpenAI(api_key=config.OPENAI_API_KEY)

def load_topics():
    """Load topics from JSON file."""
    with open('topics.json', 'r') as f:
        return json.load(f)
    

class QueryModelError(Exception):
    pass


def query_model(prompt, system_prompt=prompts.SYSTEM_PROMPT):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_completion_tokens=config.MAX_TOKENS,
        )
    except Exception as e:
        # Make it obvious to the caller and logs
        raise QueryModelError(f"OpenAI API call failed: {e}") from e

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

def run_single_trial(topic, topic_statement, condition, stance_strength, replication_id):
    """Run one experimental trial."""

    
    prompt = prompts.create_prompt(
        topic_statement,
        condition,
        stance_strength
    )
    
    response = query_model(prompt)

    print("Response:" + response)

    if not response:
        return None
    
    # parsed = parse_response(response)
    
    return {
        'topic': topic,
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
        
        for topic, topic_content in list(topics_data.items()):
            # print("Current topic:", topic)
            # print(all_topics[topic].statement)
            for condition in config.CONDITIONS:
                # For user stance conditions, vary strength
                if condition != "baseline":
                    n_reps = config.N_REPLICATIONS
                    # stance_strength = random.choice(config.STANCE_STRENGTHS)
                else:
                    # run baseline only once without stance strength
                    n_reps = 1
                    # stance_strength = None
                
                
                for rep in range(n_reps):
                    trial_count += 1
                    print(f"Trial {trial_count}/{total_trials}: {topic_content['statement']} - {condition}")

                    if condition != "baseline":
                        stance_strength = random.choice(config.STANCE_STRENGTHS)
                    else:
                        stance_strength = None
                    
                    result = run_single_trial(topic, topic_content['statement'], condition, stance_strength, rep)
                    if result:
                        results.append(result)
                    else:
                        raise RuntimeError("Error in trial execution")
                    
                    # Rate limiting
                    time.sleep(0.5)

    except Exception as e:
        print("Script stopped:", e)
        exit(1)   # optional
    
    # Save results
    os.makedirs('data', exist_ok=True)
    with open('data/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nExperiment complete! {len(results)} trials saved.")
    return results

if __name__ == "__main__":
    run_experiment()