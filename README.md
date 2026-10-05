# Sycophancy Research

Research on sycophancy in large language models — the tendency of LLMs to agree with and validate a user's stated opinions. The project combines two complementary approaches:

1. **Benchmark** — measures how model responses shift with user stance across single-turn prompts, scripted multi-turn conversations, LLM-simulated users and real-world chats, using an LLM-as-a-judge for classification (validated against human annotations).
2. **User study** — an empirical study of the effects of sycophantic LLM behavior on real users, run on a custom chat platform and analyzed in R.

## Repository structure

```
.
├── benchmark/                  # Sycophancy benchmark (Python package `sycobench`, CLI `syco`)
│   ├── src/sycobench/          # Shared schema, OpenRouter client, judge, export, and the approaches:
│   │                           #   single-turn, multi-turn (scripted users), simulated user (LLM),
│   │                           #   real-world chats, and replay of real user turns on new models
│   ├── configs/                # One YAML per experiment (models, conditions, topics, reps)
│   ├── data/                   # Topics, generated user scripts, real-world data (raw/ is gitignored)
│   ├── runs/                   # One directory per run: config, manifest, conversations, judgements
│   ├── results/                # Tidy CSV exports read by the R analyses (generated)
│   ├── analysis_R/             # Benchmark, user-study, judge-validation and cross-approach analyses
│   ├── validation/             # Judge vs. human annotation data and scripts
│   ├── legacy/                 # Frozen thesis outputs (simulation, judge, judged user-study chats)
│   └── docs/                   # Methods, judge documentation, validation approach
│
└── user-study/
    ├── platform/               # React + Firebase chat app used in the study
    │                           # (conditions via routes: /u unprompted, /s sycophantic,
    │                           #  /c contrarian, /n neutral; chats saved to Cloud Storage)
    └── analysis/               # Download / combination scripts (Python) and
                                # analyses scripts (R, for opinion change, confidence,
                                # chat content, descriptives)
```

## Getting started

Each component has its own README with setup and usage instructions:

- [benchmark/readme.md](benchmark/readme.md) — Python package (`syco run` → `syco judge` → `syco export` → R)
- [user-study/platform/README.md](user-study/platform/README.md) — web app (Node.js, Firebase CLI, deployment)
- [user-study/analysis/README.md](user-study/analysis/README.md) — analysis code

Both the benchmark and the platform query models through [OpenRouter](https://openrouter.ai/) and require an API key. For the benchmark, set it as `OPENROUTER_API_KEY` (environment variable or a `.env` file in `benchmark/`); for the platform, it is configured as a Firebase Functions secret (see the platform README).
