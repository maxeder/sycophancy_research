# Validation Approach: LLM Judge vs. Human Annotations

## Goal

Assess whether the LLM judge assigns sycophancy scores that agree with human annotations, using Cohen's Kappa as the primary agreement metric.

## Data

| File | Description |
|------|-------------|
| `validation_data/combined_data_human.json` | Human-annotated scores (combined across conditions) |
| `validation_data/combined_data_judge.json` | LLM judge scores (combined across conditions) |

Both files share the same structure: 10 cases × 9 turns, each turn containing sentence-level classifications. Scores are on an ordinal scale: **-2, -1, 0, 1, 2**.


## Unit of Analysis

The primary unit is the **sentence** (267 total, 258 after dropping nulls). Each sentence has one human score and one judge score.

## Metrics

### 1. Cohen's Kappa (primary)
- Weighted kappa with **linear weights** is the most appropriate choice here because the scale is ordinal and the cost of a 2-point disagreement should be larger than a 1-point disagreement.
- Use `sklearn.metrics.cohen_kappa_score(human_scores, judge_scores, weights='linear')`.
- Also report unweighted kappa for reference.

### 2. Supporting metrics
- **Percent exact agreement**: fraction of sentences where human score == judge score.
- **Mean absolute error (MAE)**: average |human − judge| per sentence; interpretable in scale units.
- **Confusion matrix**: 5×5 matrix (rows = human, columns = judge) to visualize systematic biases.
- **Score distribution comparison**: histogram of human vs. judge scores to detect label-frequency bias.

## Aggregation Levels

Run all metrics at three levels:

1. **Global** — all 258 sentences pooled.
2. **Per case** (10 cases) — to check whether agreement varies by topic or stance (pro vs. con).
3. **Per turn** (turns 0–8) — to check whether agreement degrades over longer conversations.

## Interpretation Guide

| Weighted Kappa | Interpretation |
|----------------|----------------|
| < 0.20 | Slight agreement |
| 0.21 – 0.40 | Fair agreement |
| 0.41 – 0.60 | Moderate agreement |
| 0.61 – 0.80 | Substantial agreement |
| > 0.80 | Almost perfect agreement |

A weighted kappa ≥ 0.60 would support using the LLM judge as a reliable automated scorer. Below 0.40 would suggest the judge needs revision.

## Limitations / Things to Watch For

- **Scale asymmetry**: the human annotator used the full -2 to 2 range; check whether the judge avoids extreme scores (-2, 2) and whether that drives disagreement.
- **Single annotator**: with only one human rater there is no human inter-rater reliability baseline; kappa reflects human–judge agreement but cannot be compared to a human–human ceiling.
