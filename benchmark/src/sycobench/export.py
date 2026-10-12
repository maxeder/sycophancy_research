"""Tidy CSV exports for R: one row per case, per turn, and per sentence.

Every row carries the run and case columns (approach, topic, user_stance, condition, ...)
plus scalar `meta_*` fields, so files from different runs and approaches can be stacked.
"""

import csv
from pathlib import Path
from typing import Iterable, Optional

from .io import load_models
from .metrics import case_row, single_turn_baselines, turn_rows
from .runs import CONVERSATIONS, judgement_path, load_config
from .schema import Conversation, Judgement


def _case_columns(run_id: str, conv: Conversation, judge_model: str) -> dict:
    return {
        "run_id": run_id, "approach": conv.approach, "case_id": conv.case_id, "topic": conv.topic,
        "user_stance": conv.user_stance, "condition": conv.condition, "attribution": conv.attribution,
        "rep": conv.rep, "target_model": conv.target_model, "judge_model": judge_model,
    }


def _meta_columns(conv: Conversation) -> dict:
    return {f"meta_{k}": v for k, v in conv.meta.items() if isinstance(v, (str, int, float, bool)) or v is None}


def run_tables(run_dir: Path, judge_model: Optional[str] = None) -> dict[str, list[dict]]:
    run_dir = Path(run_dir)
    judge_model = judge_model or load_config(run_dir).judge.model
    convs = load_models(run_dir / CONVERSATIONS, Conversation)
    path = judgement_path(run_dir, judge_model)
    if not path.exists():
        raise FileNotFoundError(f"No judgements for {judge_model} in {run_dir}; run `syco judge {run_dir}` first")
    judgements = load_models(path, Judgement)

    pairs = [(convs[cid], j) for cid, j in judgements.items() if cid in convs]
    st_baselines = single_turn_baselines(pairs)
    tables = {"cases": [], "turns": [], "sentences": []}
    for conv, judgement in pairs:
        base, meta = _case_columns(run_dir.name, conv, judge_model), _meta_columns(conv)
        tables["cases"].append({**base, **case_row(conv, judgement, st_baselines), **meta})
        for t, row in zip(judgement.turns, turn_rows(conv, judgement, st_baselines)):
            tables["turns"].append({**base, **row, **meta})
            for i, s in enumerate(t.sentences):
                tables["sentences"].append({**base, "turn": t.turn, "role": t.role, "sentence_idx": i,
                                            "sentence": s.sentence, "score": s.score, **meta})
    return tables


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = list(dict.fromkeys(k for r in rows for k in r))  # union, first-seen order
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, restval="NA")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if v is None else v) for k, v in r.items()})


def export(run_dirs: Iterable[Path], out_dir: Path, judge_model: Optional[str] = None,
           combined: Optional[str] = None) -> list[Path]:
    """Write results/<run_id>/{cases,turns,sentences}.csv, or results/<combined>_*.csv for several runs."""
    run_dirs = [Path(r) for r in run_dirs]
    all_tables = {"cases": [], "turns": [], "sentences": []}
    written = []
    for run_dir in run_dirs:
        tables = run_tables(run_dir, judge_model)
        if combined:
            for k, rows in tables.items():
                all_tables[k] += rows
        else:
            for k, rows in tables.items():
                p = out_dir / run_dir.name / f"{k}.csv"
                write_csv(p, rows)
                written.append(p)
    if combined:
        for k, rows in all_tables.items():
            p = out_dir / f"{combined}_{k}.csv"
            write_csv(p, rows)
            written.append(p)
    return written
