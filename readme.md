# syc_simulation

Script for querying an LLM across topic statements and conditions, recording model positions and reasoning.

- `experiment.py` — main runner: loads `topics.json`, constructs prompts, queries the OpenAI client, parses responses, and writes results to `data/results.json`.
- `config.py` — configuration (API key, model, conditions, replication settings, tokens, etc.).
- `prompts.py` — system and prompt templates used to generate model queries.
- `topics.json` — topic statements used for trials.
- `data/` — output directory; `results.json` stores experiment outputs.

Quick setup
Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your OpenAI API key in `config.py` (or via environment variable depending on the project config).

Run the experiment

```bash
python3 experiment.py
```

After running, results are written to `data/results.json` (JSON list containing topic, condition, stance strength, model position, reasoning, and raw response).



