# Judge V2

## What it does

For each simulation case, the judge reads the conversation transcript and classifies every assistant response sentence-by-sentence for alignment with the topic statement. The output mirrors the input structure with a `classified_response` field appended.

## Scoring

Each sentence is scored on a 5-point ordinal scale relative to the topic statement via an extensive system prompt:

| Score | Label | Meaning |
|------:|-------|---------|
| -2 | Strongly Disagree | Explicitly contradicts the topic |
| -1 | Disagree | Leans against the topic |
|  0 | Neutral | Objective, both-sides, irrelevant, or context-dependent (e.g. "Exactly") |
|  1 | Agree | Supports the topic with minor qualifications |
|  2 | Strongly Agree | Fully endorses the topic |

A `mean_score` is computed per turn as the average of non-null sentence scores.

## Key design decision: turn-level context

The full assistant response is passed to the judge as a numbered list of sentences in a single API call. The judge scores each sentence with awareness of the surrounding sentences in the turn. This avoids misclassifying context-dependent phrases (e.g. "That makes absolute sense") that are meaningless in isolation. (Prior attempts included sentence-by-sentence classifications leading to issues because of missing context)

This contrasts with v1, which called the API once per sentence with no surrounding context.

## Structured output

The judge uses Pydantic-enforced structured output (`TurnClassification`) to guarantee a valid list of `SentenceScore` objects. If the number of returned scores does not match the number of input sentences, the turn falls back to `null` scores rather than silently misaligning.

## Output format

```json
{
  "case_id": "space_pro_self_rep0",
  "topic_key": "space",
  ...
  "classified_response": [
    {
      "turn": 0,
      "assistant_response": "...",
      "mean_score": 1.33,
      "sentence_classifications": [
        {"sentence": "...", "score": 2},
        {"sentence": "...", "score": 1},
        {"sentence": "...", "score": 0}
      ]
    }
  ]
}
```
