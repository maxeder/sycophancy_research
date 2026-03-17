# compute mean scores on human-annotated validation set for comparison with LLM judge results

import json


INPUT_FILE = 'human_annotation_data/val_unprompted_judge_results_multiturn_gemini-2.5-flash_human_eval.json'


# Load the dataset
with open(INPUT_FILE, 'r') as f:
    data = json.load(f)


# Calculate mean score from sentence classifications
total_score = 0
total_count = 0

for item in data:
    print(item)
    class_response = item.get('classified_response', [])
    for turn in class_response:
        sentence_classifications = turn.get('sentence_classifications', [])
        total_score = 0
        
        for sentence in sentence_classifications:
            score = sentence.get('score')
            if score is not None:
                total_score += score
                total_count += 1


        mean_score = total_score / len(sentence_classifications) if total_count > 0 else 0


        turn['mean_score'] = mean_score
#     if 'sentence_classification' in item:
#         for classification in item['sentence_classification']:
#             if 'score' in classification:
#                 total_score += classification['score']
#                 total_count += 1

# mean_score = total_score / total_count if total_count > 0 else 0
# print(f"Mean score: {mean_score}")
