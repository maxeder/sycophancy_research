"""syco: generate | run | judge | export | import-legacy

  syco generate configs/generate_scripts.yaml          # LLM-written user scripts for multi-turn
  syco run configs/multi_turn_thesis.yaml --limit 2     # new run directory under runs/
  syco run --resume runs/<run_id>                       # continue / retry failed cases
  syco judge runs/<run_id> [--model google/gemini-2.5-flash]
  syco export runs/<run_id> [runs/<other> ...] [--combined all]
  syco import-legacy                                    # thesis outputs -> runs/legacy_*
"""

import argparse
from pathlib import Path

from .config import GenerateScriptsConfig, find_root, load_run_config, load_yaml


def _client():
    from .llm import OpenRouterClient
    return OpenRouterClient()


def cmd_generate(args):
    from .approaches.multi_turn import generate_scripts
    raw, root = load_yaml(args.config)
    out = generate_scripts(GenerateScriptsConfig(**raw), root, _client(), limit=args.limit)
    print(f"Scripts written to {out}")


def cmd_run(args):
    from .approaches import APPROACHES
    from .runner import make_approach, run
    from .runs import load_config
    run_dir = None
    if args.resume:
        run_dir = Path(args.resume).resolve()
        cfg, root = load_config(run_dir), find_root(run_dir)
    else:
        if not args.config:
            raise SystemExit("syco run: give a config, or --resume RUN_DIR")
        cfg, root = load_run_config(args.config)
        if args.dry_run:
            cases = make_approach(cfg, root).build_cases()
            print(f"{cfg.approach}: {len(cases)} cases")
            for c in cases[: args.limit or 10]:
                print(" ", c.case_id)
            return
    client = _client() if APPROACHES[cfg.approach].needs_target else None
    run(cfg, root, client, resume=run_dir, limit=args.limit)


def cmd_judge(args):
    from .judge import judge_run
    from .runs import load_config
    run_dir = Path(args.run_dir).resolve()
    cfg = load_config(run_dir).judge
    if args.model:
        cfg = cfg.model_copy(update={"model": args.model})
    judge_run(run_dir, find_root(run_dir), _client(), cfg, limit=args.limit)


def cmd_export(args):
    from .export import export
    run_dirs = [Path(r).resolve() for r in args.run_dirs]
    out = Path(args.out).resolve() if args.out else find_root(run_dirs[0]) / "results"
    for p in export(run_dirs, out, judge_model=args.judge, combined=args.combined):
        print(f"✓ {p}")


def cmd_import_legacy(args):
    from .legacy import import_legacy
    import_legacy(find_root(Path.cwd()))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="syco", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("generate", help="generate scripted user turns for the multi-turn approach")
    p.add_argument("config")
    p.add_argument("--limit", type=int, help="only the first N scripts")
    p.set_defaults(fn=cmd_generate)

    p = sub.add_parser("run", help="run an approach and write conversations to a run directory")
    p.add_argument("config", nargs="?")
    p.add_argument("--resume", help="existing run directory to continue")
    p.add_argument("--limit", type=int, help="only the first N cases")
    p.add_argument("--dry-run", action="store_true", help="list cases without calling any model")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("judge", help="score a run's conversations with the LLM judge")
    p.add_argument("run_dir")
    p.add_argument("--model", help="override the judge model from the run config")
    p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("export", help="write tidy CSVs (cases/turns/sentences) for R")
    p.add_argument("run_dirs", nargs="+")
    p.add_argument("--judge", help="judge model whose scores to export (default: the run config's judge)")
    p.add_argument("--out", help="output directory (default: results/)")
    p.add_argument("--combined", metavar="NAME", help="stack all runs into results/NAME_{cases,turns,sentences}.csv")
    p.set_defaults(fn=cmd_export)

    p = sub.add_parser("import-legacy", help="convert legacy/ thesis outputs into runs/legacy_*")
    p.set_defaults(fn=cmd_import_legacy)

    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
