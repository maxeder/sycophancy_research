# compute mean scores on human-annotated validation set for comparison with LLM judge results

import json


INPUT_FILE = 'annotation_data/comparison_data_human_sycophantic.json'
OUTPUT_FILE = 'annotation_data/comparison_data_human_sycophantic.json'


# Load the dataset
with open(INPUT_FILE, 'r') as f:
    data = json.load(f)


# Calculate mean score from sentence classifications
total_score = 0
total_count = 0

for item in data:
    # print(item)
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

# save json with mean scores added
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f, indent=2)