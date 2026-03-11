# syc_simulation — Codebase Overview

## Purpose

This is a **sycophancy simulation framework** — a research tool for studying whether LLMs exhibit sycophantic behavior (agreeing with users even when incorrect) by running controlled multi-turn conversations and measuring how model responses shift based on user stance.

---

## Pipeline (3 stages)

### 1. `userdata_generator.py` — Synthetic User Data Generation
- Uses an LLM (via OpenRouter) to generate realistic multi-turn user conversation scripts
- For each topic, generates scripts for **Pro** and **Con** stances, across attribution styles (`self`, `expert`, `consensus`, `authority`)
- Turn 0 is always a neutral baseline ("What is your stance on X?"), followed by N opinion-expressing turns
- Output: `userdata_output/userdata_*.json`

### 2. `simulator_multiturn.py` — Simulation
- Takes synthetic user data and feeds it turn-by-turn to a **target model**, maintaining full conversation history
- Three **system prompt modes** (set via CLI flags):
  - `--unprompted`: neutral default assistant
  - `--syc`: sycophantic (validate user's beliefs)
  - `--cont`: contrarian (challenge user's beliefs)
- Output: `simulation_output/{mode}_results_multiturn_*.json` — full transcripts

### 3. `judge.py` — LLM-as-a-Judge Classification
- Takes simulation transcripts and classifies each assistant sentence on a **-2 to +2 Likert scale** of agreement with the topic statement
- Uses `pysbd` for sentence splitting, structured output via Pydantic
- Currently judge model: `gemini-2.5-flash` via OpenRouter
- Output: `judge_output/{mode}_judge_results_multiturn_*.json`

---

## Key Files

| File | Role |
|------|------|
| `config.py` | All model settings (target, judge, userdata-gen models, API keys, replication counts) |
| `prompts.py` | System prompt templates (default/sycophantic/contrarian) + stance phrases |
| `utils.py` | JSONL append, JSONL→JSON conversion, JSON loading |
| `topics/sel_topics.json` | Selected topic questions with pro/con stances and about-phrases |
| `simulator_singleturn.py` | Older single-turn variant (not the main pipeline) |

---

## Analysis
- `analysis_python/` — Python scripts + HTML visualizations
- `analysis_R/` — R scripts and plots for statistical analysis

---

## Current Config
- **Target model**: `openai/gpt-5.2` via OpenRouter
- **Judge model**: `google/gemini-2.5-flash`
- **Replications**: 2 per condition
- **Turns per conversation**: 8 (+ 1 baseline)
