# Sycophancy Benchmark

Measures how far a model's stance moves towards a user's opinion, using four approaches that share one record format, one LLM judge and one export:

| Approach | Where the user turns come from | Config |
|---|---|---|
| `single_turn` | one templated prompt: a baseline question, or a stance (weak/moderate/strong) followed by the question | `configs/single_turn.yaml` |
| `multi_turn` | a pre-generated script of user messages (`syco generate`) | `configs/multi_turn_thesis.yaml` |
| `simulated_user` | an LLM playing a user with escalating persuasion tactics, reacting to each reply | `configs/simulated_user.yaml` |
| `real_world` | recorded human chats, judged as recorded (no model calls) | `configs/real_world_userstudy.yaml` |
| `replay` | recorded human messages sent to a new target model | `configs/replay_userstudy.yaml` |

Each approach produces conversations. The judge rates every sentence's agreement with the topic statement from -2 to +2 (see [docs/judge_doc.md](docs/judge_doc.md)). `syco export` then writes tidy CSVs that the R analyses read.

## Setup

```bash
cd benchmark
uv venv && uv pip install -e '.[dev,validation]'   # or: python -m venv .venv && pip install -e '.[dev,validation]'
source .venv/bin/activate
```

Set `OPENROUTER_API_KEY` in your environment or in `benchmark/.env`. All models are OpenRouter ids such as `openai/gpt-5.2`.

## Workflow

```bash
syco run configs/multi_turn_thesis.yaml --dry-run      # list the cases without calling any model
syco run configs/multi_turn_thesis.yaml --limit 2      # creates runs/<date>_<name>_<target>_<hash>/
syco run --resume runs/<run_id>                        # continue a run or retry failed cases (see errors.jsonl)
syco judge runs/<run_id>                               # judge model and roles come from the run config
syco judge runs/<run_id> --model anthropic/claude-sonnet-4.6   # a second judge, stored next to the first
syco export runs/<run_id>                              # writes results/<run_id>/{cases,turns,sentences}.csv
syco export runs/<a> runs/<b> --combined all           # stacks several runs into results/all_*.csv
syco generate configs/generate_scripts.yaml            # new user scripts for multi_turn, written to data/scripts/
```

To compare models, copy a config and change `target.model`. To compare approaches, keep the topics, `conditions` and judge the same, then use `--combined` and [analysis_R/cross_approach.Rmd](analysis_R/cross_approach.Rmd).

**Conditions** are the target's system prompt: `none` (no system prompt), `unprompted`, `sycophantic` or `contrarian`. The prompt texts are in [src/sycobench/prompts/target_system.py](src/sycobench/prompts/target_system.py).

**Turns** are numbered per dialogue turn: a user message and the reply to it share one number. Turn 0 is the baseline, meaning the neutral opening question, or the platform greeting in user-study chats. Single-turn baseline cases are turn 0 and stance cases are turn 1.

**Case ids** are deterministic, e.g. `multi_turn:space:pro:sycophantic:self:3`. This lets you line up a re-run with the thesis run case by case.

## Run directory

```
runs/<run_id>/
├── config.resolved.yaml     # the full config the run used
├── manifest.json            # git commit, models, counts, judges
├── conversations.jsonl      # one Conversation per line (src/sycobench/schema.py)
├── errors.jsonl             # failed cases (retried by --resume)
└── judgements/<judge>.jsonl # one Judgement per line, per judge model
```

Runs are append-only: resuming never overwrites, and when a case appears more than once in a jsonl file, the last line wins. New runs are not gitignored, so commit the finished ones you want to keep.

## Export columns (for R)

`turns.csv` has one row per judged turn. It contains:
- the case columns (`run_id, approach, case_id, topic, user_stance, condition, attribution, rep, target_model, judge_model`)
- `turn, role, mean_score, n_sentences, n_scored`
- `aligned_score`: the score flipped for users arguing "con", so +2 always means full agreement with the user
- `baseline_score`, `delta_from_baseline`, `aligned_delta`
- `meta_*` fields, such as the user study's `meta_pre_opinion`

`cases.csv` adds per-case summaries: `final_score`, `aligned_delta_final`, `aligned_drift` and `flipped`. `sentences.csv` has one row per scored sentence.

## Thesis data (legacy)

The thesis outputs are kept unchanged in `legacy/`:
- `simulation_output/` and `judge_output/`: the multi-turn run, GPT-5.2 judged by Gemini 2.5 Flash
- `user_study/user_study_judged.json`

To reproduce the thesis analyses without any API calls:

```bash
syco import-legacy                 # creates runs/legacy_multi_turn_thesis and runs/legacy_user_study
syco export runs/legacy_multi_turn_thesis runs/legacy_user_study
# then knit analysis_R/benchmark_analysis.Rmd and analysis_R/userstudy_analysis.Rmd
```

Figures go to `analysis_R/figures/` by default. Set `SYCO_FIGURES_DIR` to write them into the manuscript's Figures folder instead.

To re-run the thesis benchmark with the new code, use `configs/multi_turn_thesis.yaml`. It uses the same scripts (`data/scripts/new_data_8_turns_openai_gpt-5.2.json`), prompts, models and temperatures.

| Old script | Now |
|---|---|
| `userdata_generator.py` | `syco generate configs/generate_scripts.yaml` |
| `simulator_multiturn.py --syc` etc. | `syco run configs/multi_turn_thesis.yaml` (all conditions in one run) |
| `simulator_singleturn.py` | `syco run configs/single_turn.yaml` |
| `simulator_llmuser.py` | `syco run configs/simulated_user.yaml` |
| `judge.py`, `judge_userstudy.py`, `turn_fix.py` | `syco judge` (set `judge.roles` to include user turns) |
| `config.py`, `prompts.py` | `configs/*.yaml`, `src/sycobench/prompts/` |

## Layout

```
benchmark/
├── src/sycobench/
│   ├── schema.py              # Conversation, Turn, Judgement
│   ├── config.py              # RunConfig / JudgeConfig / GenerateScriptsConfig (YAML)
│   ├── llm.py                 # the only OpenRouter client (retries, structured output)
│   ├── approaches/            # single_turn, multi_turn (+ generate_scripts), simulated_user,
│   │   └── real_world/        #   real_world adapters (user_study, conversations) and replay
│   ├── prompts/               # target system prompts, single-turn, user scripts, user sim, judge
│   ├── runner.py / runs.py    # shared run loop, run directories, manifest
│   ├── judge.py               # sentence-level LLM judge
│   ├── metrics.py / export.py # aligned scores, drift, flips; tidy CSVs
│   ├── legacy.py              # thesis outputs -> run directories
│   └── cli.py                 # `syco`
├── configs/                   # one YAML per experiment
├── data/
│   ├── topics/                # sel_topics.json (5 topics), all_topics.json, sel_topics_inverse.json
│   ├── scripts/               # generated user scripts for multi_turn
│   └── real_world/            # raw/ (gitignored: may contain identifiers), processed/ (anonymised)
├── runs/                      # run directories (legacy_* are gitignored and rebuilt by import-legacy)
├── results/                   # exported CSVs (gitignored, rebuilt by export)
├── analysis_R/                # benchmark, user-study, judge-validation and cross-approach analyses
├── validation/                # judge vs. human annotation (annotation_data/, validation_data/, scripts)
├── legacy/                    # frozen thesis outputs
├── docs/                      # methods, judge documentation, validation approach, notes
└── tests/                     # pytest with a fake LLM client (no API calls)
```

## Adding real-world data

Write an adapter in `src/sycobench/approaches/real_world/` that yields `Conversation`s, and register it with `@register("name")`. `user_study.py` is the example to follow. An adapter keeps only the fields that are safe to store; raw files with identifiers go in `data/real_world/raw/`. Alternatively, convert a dataset once into anonymised Conversation jsonl in `data/real_world/processed/` and use `adapter: conversations`.

## Tests

```bash
pytest
```

The tests cover every approach, resume, the judge's retry of failed turns, the export, and loading the legacy thesis files into the new schema. They use a fake client and make no API calls.
