import json
import csv
import os
import glob

CHATS_DIR = "chats"
CSV_PATH = "data/full_data.csv"
OUTPUT_PATH = "all_chats.json"

# Pre/post opinion column mapping per topic
PRE_COLS = {
    "quota": "pre_quota",
    "taxes": "pre_taxes",
    "animals": "pre_animals",
    "speech": "pre_speech",
    "space": "space_02",
}
POST_COLS = {
    "quota": "post_quota",
    "taxes": "post_taxes",
    "animals": "post_animals",
    "speech": "post_speech",
    "space": "post_space_04",
}

# Load CSV into a dict keyed by CASE number
survey = {}
with open(CSV_PATH, encoding="utf-16-le") as f:
    reader = csv.DictReader(f, delimiter="\t")
    case_col = reader.fieldnames[0]  # BOM-prefixed "CASE"
    for row in reader:
        survey[row[case_col].strip()] = row

# Process all chat files
all_chats = []
for filepath in sorted(glob.glob(os.path.join(CHATS_DIR, "*.json"))):
    filename = os.path.basename(filepath)
    # Parse filename
    name = filename.removesuffix(".json")
    parts = name.split("-", 2)
    case_id = parts[0]
    topic = parts[1]
    condition = parts[2]

    with open(filepath) as f:
        transcript = json.load(f)

    # Look up pre/post opinion from CSV
    row = survey.get(case_id)
    if row is None:
        print(f"WARNING: case {case_id} not found in CSV, skipping {filename}")
        continue

    pre_col = PRE_COLS[topic]
    post_col = POST_COLS[topic]
    pre_val = row.get(pre_col, "")
    post_val = row.get(post_col, "")

    pre_opinion = int(pre_val) if pre_val.strip() else None
    post_opinion = int(post_val) if post_val.strip() else None

    all_chats.append({
        "case_id": name,
        "case": int(case_id),
        "condition": condition,
        "topic": topic,
        "pre_opinion": pre_opinion,
        "post_opinion": post_opinion,
        "transcript": transcript,
    })

with open(OUTPUT_PATH, "w") as f:
    json.dump(all_chats, f, indent=4)

print(f"Combined {len(all_chats)} chats into {OUTPUT_PATH}")
