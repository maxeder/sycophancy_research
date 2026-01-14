# syc_simulation

Script for querying an LLM across topic statements and conditions, recording model positions and reasoning.

- `simulator.py` — run simulations
- `judge.py` — classify simulation outputs
- `config.py` — configuration (API key, model, conditions, replication settings, tokens, etc.)
- `prompts.py` — system and prompt templates used to generate model queries
- `topics/` — topic questions and statements
- `simulation_output/` — stores simulation outputs
- `judge_output/` — stores judge outputs

## Setup
Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set OpenRouter API key in `config.py` (or via environment variable)


## Run the simulation

```bash
python3 simulation.py
```

After running, results are written to `simulation_output/results_{provider}_{model}.json` (JSON containing topic, topic_strength, condition, stance strength, rep_counter and response).


## Classify simulation output

```bash
python3 judge.py
```
Using LLM-as-a-judge approach, classify the output of the simulation into (agree | neutral | disagree)



