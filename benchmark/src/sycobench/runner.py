"""Run an approach: build cases, skip those already in the run directory, and write conversations."""

import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from . import __version__
from .approaches import APPROACHES, Approach
from .config import RunConfig
from .io import append_jsonl, read_records
from .llm import ChatClient
from .runs import CONVERSATIONS, ERRORS, config_hash, git_info, load_config, new_run_dir, update_manifest


def make_approach(cfg: RunConfig, root: Path) -> Approach:
    return APPROACHES[cfg.approach](cfg, root)


def run(
    cfg: Optional[RunConfig],
    root: Path,
    client: Optional[ChatClient],
    resume: Optional[Path] = None,
    limit: Optional[int] = None,
) -> Path:
    if resume:
        run_dir = Path(resume)
        cfg = load_config(run_dir)
    else:
        run_dir = new_run_dir(root, cfg)

    approach = make_approach(cfg, root)
    cases = approach.build_cases()
    if limit is not None:
        cases = cases[:limit]

    out = run_dir / CONVERSATIONS
    done = {r["case_id"] for r in read_records(out)}
    todo = [c for c in cases if c.case_id not in done]

    update_manifest(
        run_dir,
        sycobench_version=__version__,
        name=cfg.name,
        approach=cfg.approach,
        target_model=cfg.target.model if cfg.target else None,
        config_hash=config_hash(cfg),
        git=git_info(root),
        n_cases=len(cases),
        started=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    print(f"{cfg.approach}: {len(cases)} cases, {len(done)} already done, {len(todo)} to run -> {run_dir}")

    def one(case):
        conv = approach.run_case(case, client)
        append_jsonl(out, conv)
        return case.case_id

    n_errors = 0
    with ThreadPoolExecutor(max_workers=max(1, cfg.concurrency)) as pool:
        futures = {pool.submit(one, c): c for c in todo}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=cfg.name):
            try:
                fut.result()
            except Exception as e:
                n_errors += 1
                case = futures[fut]
                append_jsonl(run_dir / ERRORS, {"case_id": case.case_id, "error": repr(e), "traceback": traceback.format_exc()})
                print(f"✗ {case.case_id}: {e}")

    n_done = len({r["case_id"] for r in read_records(out)})
    update_manifest(run_dir, n_done=n_done, n_errors_last_session=n_errors,
                    finished=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print(f"✓ {n_done}/{len(cases)} conversations in {out}" + (f" ({n_errors} errors, see {ERRORS}; rerun with --resume)" if n_errors else ""))
    return run_dir
