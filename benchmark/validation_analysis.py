"""
Validation: LLM judge vs. human annotation agreement
Primary metric: linear weighted Cohen's Kappa (sentence-level)
"""

import json
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix

HUMAN_FILE = 'annotation_data/comparison_human_data.json'
JUDGE_FILE = 'annotation_data/comparison_data_judge.json'
LABELS = [-2, -1, 0, 1, 2]


def load_paired_scores(human_data, judge_data):
    """Return aligned (human, judge) score lists at sentence level, with metadata."""
    judge_index = {e['case_id']: e for e in judge_data}
    records = []  # (human_score, judge_score, case_id, turn, sentence)
    for h_entry in human_data:
        cid = h_entry['case_id']
        j_entry = judge_index[cid]
        j_turns = {t['turn']: t for t in j_entry['classified_response']}
        for h_turn in h_entry['classified_response']:
            turn_num = h_turn['turn']
            j_turn = j_turns[turn_num]
            for h_sent, j_sent in zip(
                h_turn['sentence_classifications'],
                j_turn['sentence_classifications']
            ):
                records.append({
                    'human': h_sent['score'],
                    'judge': j_sent['score'],
                    'case_id': cid,
                    'turn': turn_num,
                    'sentence': h_sent['sentence'],
                })
    return records


def kappa_stats(human, judge):
    kw = cohen_kappa_score(human, judge, weights='linear', labels=LABELS)
    k  = cohen_kappa_score(human, judge, weights=None,     labels=LABELS)
    mae = np.mean(np.abs(np.array(human) - np.array(judge)))
    pct_exact = np.mean(np.array(human) == np.array(judge))
    return dict(weighted_kappa=kw, kappa=k, mae=mae, pct_exact=pct_exact, n=len(human))


def fmt(stats):
    return (f"  weighted κ = {stats['weighted_kappa']:.3f} | "
            f"κ = {stats['kappa']:.3f} | "
            f"MAE = {stats['mae']:.3f} | "
            f"exact = {stats['pct_exact']:.1%} | "
            f"n = {stats['n']}")


def print_confusion(human, judge):
    cm = confusion_matrix(human, judge, labels=LABELS)
    header = "       " + "  ".join(f"J={l:+d}" for l in LABELS)
    print(header)
    for i, row in enumerate(cm):
        print(f"  H={LABELS[i]:+d}  " + "   ".join(f"{v:4d}" for v in row))


def score_dist(scores, label):
    counts = {l: scores.count(l) for l in LABELS}
    total = len(scores)
    parts = "  ".join(f"{l:+d}: {counts[l]:3d} ({counts[l]/total:.1%})" for l in LABELS)
    print(f"  {label}: {parts}")


# ── Load ──────────────────────────────────────────────────────────────────────
with open(HUMAN_FILE) as f:
    human_data = json.load(f)
with open(JUDGE_FILE) as f:
    judge_data = json.load(f)

records = load_paired_scores(human_data, judge_data)
human_all = [r['human'] for r in records]
judge_all = [r['judge'] for r in records]

# ── Global ────────────────────────────────────────────────────────────────────
print("=" * 70)
print("GLOBAL")
print("=" * 70)
print(fmt(kappa_stats(human_all, judge_all)))

print("\nScore distributions:")
score_dist(human_all, "human")
score_dist(judge_all, "judge")

print("\nConfusion matrix (rows = human, cols = judge):")
print_confusion(human_all, judge_all)

# ── Per case ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PER CASE")
print("=" * 70)
case_ids = [e['case_id'] for e in human_data]
for cid in case_ids:
    subset = [r for r in records if r['case_id'] == cid]
    h = [r['human'] for r in subset]
    j = [r['judge'] for r in subset]
    print(f"\n{cid}")
    print(fmt(kappa_stats(h, j)))

# ── Per turn ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PER TURN")
print("=" * 70)
max_turn = max(r['turn'] for r in records)
for turn in range(max_turn + 1):
    subset = [r for r in records if r['turn'] == turn]
    h = [r['human'] for r in subset]
    j = [r['judge'] for r in subset]
    print(f"\nTurn {turn}")
    print(fmt(kappa_stats(h, j)))
