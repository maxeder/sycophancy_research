# prepare a version of the judge results with scores stripped for human annotation, keeping only one pro and one con per topic (rep_counter == 0)

import json


INPUT_FILE = 'judge_output/unprompted_judge_results_multiturn_gemini-2.5-flash.json'
# OUTPUT_FILE = 'human_annotation_data/val_unprompted_judge_results_multiturn_gemini-2.5-flash_human_eval.json'

OUTPUT_FILE = 'human_annotation_data/comparison_data_judge.json'

# Load the dataset
with open(INPUT_FILE, 'r') as f:
    data = json.load(f)

# Keep only one pro and one con per topic (rep_counter == 0)
filtered = [e for e in data if e['rep_counter'] == 0]

output = []
for entry in filtered:
    # Strip scores from classified_response for human annotation
    cleaned_classified = []
    for turn in entry.get('classified_response', []):
        cleaned_turn = {
            'turn': turn['turn'],
            'assistant_response': turn['assistant_response'],
            'mean_score': turn['mean_score'],
            'sentence_classifications': [
                {'sentence': s['sentence'], 'score': s['score']}
                for s in turn.get('sentence_classifications', [])
            ]
        }
        cleaned_classified.append(cleaned_turn)

    output.append({
        'case_id': entry['case_id'],
        'topic_key': entry['topic_key'],
        'topic_question': entry['topic_question'],
        'user_stance': entry['user_stance'],
        'classified_response': cleaned_classified
    })

with open(OUTPUT_FILE, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved {len(output)} entries")
