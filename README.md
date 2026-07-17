# Sycophancy Research

Research on sycophancy in large language models — the tendency of LLMs to agree with and validate a user's stated opinions. The project combines two complementary approaches:

1. **Benchmark** — a simulation framework that measures how model responses shift with user stance in controlled multi-turn conversations, using an LLM-as-a-judge for classification (validated against human annotations).
2. **User study** — an empirical study of the effects of sycophantic LLM behavior on real users, run on a custom chat platform and analyzed in R.

## Repository structure

```
.
├── benchmark/                  # Sycophancy simulation & measurement pipeline
│   ├── userdata_generator.py   # Generate synthetic multi-turn user scripts (pro/con stances)
│   ├── simulator_multiturn.py  # Run target model under unprompted/sycophantic/contrarian system prompts
│   ├── simulator_singleturn.py # Older single-turn variant
│   ├── judge.py                # LLM-as-a-judge: rate agreement per sentence (-2..+2 Likert)
│   ├── judge_userstudy.py      # Apply the judge to user-study chat data
│   ├── config.py / prompts.py  # Model settings, system prompt templates, stance phrases
│   ├── topics/                 # Topic questions with pro/con stances
│   ├── userdata_output/        # Generated user prompts
│   ├── simulation_output_final/# Simulation transcripts per condition
│   ├── judge_output_final/     # Judge classifications per condition
│   ├── annotation_data/        # Judge validation against human annotators per condition
│   ├── validation_data/        # Combined validation data across conditions
│   ├── user_study_data/        # User-study chats & judged results (input/output of judge_userstudy.py)
│   ├── analysis_R/             # Statistical analysis of benchmark & validation data
│   └── *.md                    # Methods, judge documentation, validation approach
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

- [benchmark/readme.md](benchmark/readme.md) — Python pipeline (venv, OpenRouter API key, run generator → simulator → judge)
- [user-study/platform/README.md](user-study/platform/README.md) — web app (Node.js, Firebase CLI, deployment)
- [user-study/analysis/README.md](user-study/analysis/README.md) — analysis code

Both the benchmark and the platform query models through [OpenRouter](https://openrouter.ai/) and require an API key. For the benchmark, set it as `OPENROUTER_API_KEY` (environment variable or a `.env` file in `benchmark/`); for the platform, it is configured as a Firebase Functions secret (see the platform README).
