# Sycophancy Benchmark

Script for querying an LLM across topic statements and conditions, recording model positions and reasoning.

- `simulator.py` — run simulations
- `userdata_generator.py` — generate synthetic user data
- `judge.py` — classify simulation outputs
- `config.py` — configuration (API key, model, conditions, replication settings, tokens, etc.)
- `prompts.py` — system and prompt templates used to generate model queries
- `topics/` — topic questions and statements
- `simulation_output/` — stores simulation outputs
- `judge_output/` — stores judge outputs
- `userdata_output/` — stores generated user prompts

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

Set OpenRouter API key (via environment variable / .env file)

Set model provider, model and number of replications in `config.py`


## Generate synthetic user data (optional)

```bash
python3 userdata_generator.py
```
Generates user prompts used as input for the simulation. After running, results are written to `userdata_output/data_{provider}_{model}.json` (JSON containing case_id, topic, user_stance and a list of prompt turns).
*Optional: Specify trigger types with different "pressure" (preference, authority, social proof, morality, binary).*


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



