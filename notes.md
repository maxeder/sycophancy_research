TODO (possible extensions):
- add and analyse reasoning
    - Reasoning: [Your explanation]
- stance strength all conditions
    - right now it is randomized
- use the 4 generated statements instead of the pure question
    - rewrite the NF questions to positively framed to avoid double negations
- randomize order
- multi-turn
    - see if model follows user stance over multiple turns (follow "wave" of agreement / disagreement)
- what happens if model stance is prompted in system prompt, does the model stil flip to support user?
- investigate steerability (to approximate a non-sycophantic model)
- add other topics, see how more / less polarising topics influence sycophancy






Sketch for multi-turn simulation using synthetic user data:
- read in data from "userdata_output"
- go through every item in json list
    - use as user input




Maurice feedback:
- do only one trigger type
- same(ish) user prompt over multiple turns should be okay for a start
