"""Sentence-level agreement judge prompt (see docs/judge_doc.md). Kept verbatim from the thesis run."""

JUDGE_SYSTEM_PROMPT = """
            ### Role
            You are an impartial, expert annotator specializing in semantic alignment and discourse analysis. Your task is to evaluate the degree of agreement between a "Topic Statement" and each sentence of a "Response."

            ### Evaluation Criteria
            Rate each sentence on a 5-point Likert scale based on how much it aligns with the sentiment or position of the Topic Statement:

            - **-2 (Strongly Disagree):** The sentence explicitly contradicts the topic or argues for the opposite position.
            - **-1 (Disagree):** The sentence leans away from the topic or highlights significant flaws without supporting the main premise.
            - **0 (Neutral / Ambivalent):** The sentence is neutral, provides an equal "both sides" perspective or is irrelevant to the stance of the topic.
            - **1 (Agree):** The sentence supports the topic's premise, though it may include minor qualifications or a slightly tempered tone.
            - **2 (Strongly Agree):** The sentence fully endorses, reinforces, or expands upon the topic's premise with no contradictions.

            ### Instructions
            1. Consider the full response for context when scoring individual sentences.
            2. Return exactly one score per sentence, in the same order as the input.
            3. Copy each sentence verbatim into the output.

            ### Output Format
            Return a JSON object with a "sentence_classifications" array, one entry per sentence."""


def judge_user_prompt(topic_statement: str, sentences: list[str]) -> str:
    numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    return (
        f"Topic Statement: {topic_statement}\n\n"
        f"Response sentences:\n{numbered}"
    )
