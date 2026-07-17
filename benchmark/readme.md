# Sycophancy Benchmark

Pipeline for querying an LLM across topic statements and conditions (unprompted / sycophantic / contrarian), recording and classifying model positions.

- `userdata_generator.py` — generate synthetic multi-turn user data
- `simulator_multiturn.py` — run the target model over the user data per condition (main pipeline)
- `simulator_singleturn.py` — older single-turn variant (superseded)
- `judge.py` — classify simulation outputs (LLM-as-a-judge)
- `judge_userstudy.py` — apply the same judge to user-study chat data
- `validation_prep.py` / `validation_analysis.py` — prepare and analyze judge-vs-human validation (see `validation_approach.md`)
- `config.py` — configuration (API key, models, conditions, replication settings, tokens, etc.)
- `prompts.py` — system and prompt templates used to generate model queries
- `topics/` — topic questions and statements
- `userdata_output/` — generated user prompts
- `simulation_output_final/` — simulation outputs per condition
- `judge_output_final/` — judge outputs per condition
- `annotation_data/` / `validation_data/` — human-annotation validation data (per condition / combined)
- `analysis_R/` — statistical analysis (R)

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

Set the OpenRouter API key as `OPENROUTER_API_KEY` (environment variable or a `.env` file in this directory).
Set model provider, model and number of replications in `config.py`


## Generate synthetic user data (optional)

```bash
python3 userdata_generator.py            # add --testing for a single-iteration dry run
```
Generates user prompts used as input for the simulation. Results are written to `userdata_output/new_data_{n_turns}_turns_{provider}_{model}.json` (case_id, topic, user_stance and a list of prompt turns).


## Run the simulation

```bash
python3 simulator_multiturn.py --unprompted   # or --syc / --cont; --testing for a dry run
```

Runs one condition per invocation. Results are written to `simulation_output_final/{condition}_results_multiturn_{provider}_{model}.json`. The input user-data file is set via `INPUT_FILE` at the top of the script.


## Classify simulation output

```bash
python3 judge.py                         # --testing for a single-iteration dry run
```
Classifies the simulation output sentence-by-sentence using an LLM-as-a-judge (see `judge_doc.md`). The condition is selected by editing `INPUT_PATH` / `OUTPUT_PATH` at the top of the script; results are written to `judge_output_final/{condition}_judge_results_multiturn_{judge_model}.json`.
