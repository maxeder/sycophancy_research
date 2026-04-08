"""Fix turn numbering in already-judged user study data.

Changes per-message turn indices to dialogue-level turns,
where user + assistant = 1 turn (assistant greeting = turn 0).
"""

import json
import sys

INPUT_PATH = "user_study_data/user_study_judged.json"

def fix_turns(data):
    for case in data:
        classified = case.get("classified_response", [])
        turn_num = 0
        for entry in classified:
            if entry.get("role") == "user":
                turn_num += 1
            entry["turn"] = turn_num
    return data

def main():
    with open(INPUT_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} cases from {INPUT_PATH}")

    data = fix_turns(data)

    with open(INPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Fixed turn numbering and saved to {INPUT_PATH}")

if __name__ == "__main__":
    main()
