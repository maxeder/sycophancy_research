"""Run directories: runs/<date>_<name>_<target>_<hash>/ with the resolved config, a manifest,
conversations.jsonl and judgements/<judge>.jsonl. A run is never overwritten; resuming appends."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from .config import RunConfig

CONVERSATIONS = "conversations.jsonl"
ERRORS = "errors.jsonl"
CONFIG = "config.resolved.yaml"
MANIFEST = "manifest.json"


def slug(model: Optional[str]) -> str:
    return (model or "recorded").replace("/", "_")


def config_hash(cfg: RunConfig) -> str:
    return hashlib.sha1(cfg.model_dump_json().encode()).hexdigest()[:6]


def git_info(root: Path) -> dict:
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "--", "src", "configs"))}


def new_run_dir(root: Path, cfg: RunConfig) -> Path:
    date = datetime.now().strftime("%Y-%m-%d")
    run_dir = root / "runs" / f"{date}_{cfg.name}_{slug(cfg.target.model if cfg.target else None)}_{config_hash(cfg)}"
    if run_dir.exists():
        raise FileExistsError(f"{run_dir} exists; resume it with `syco run --resume {run_dir}`")
    run_dir.mkdir(parents=True)
    write_config(run_dir, cfg)
    return run_dir


def write_config(run_dir: Path, cfg: RunConfig) -> None:
    with open(run_dir / CONFIG, "w") as f:
        yaml.safe_dump(cfg.model_dump(), f, sort_keys=False, allow_unicode=True)


def load_config(run_dir: Path) -> RunConfig:
    with open(run_dir / CONFIG) as f:
        return RunConfig(**yaml.safe_load(f))


def update_manifest(run_dir: Path, **fields) -> dict:
    path = run_dir / MANIFEST
    manifest = json.loads(path.read_text()) if path.exists() else {}
    manifest.update(fields)
    manifest["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def judgement_path(run_dir: Path, judge_model: str) -> Path:
    return run_dir / "judgements" / f"{slug(judge_model)}.jsonl"
