import json
import threading
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_write_lock = threading.Lock()


def load_json(path: str | Path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path) as f:
        return json.load(f)


def read_records(path: str | Path) -> list[dict]:
    """Read a .json list or a .jsonl file."""
    path = Path(path)
    if path.suffix == ".jsonl":
        if not path.exists():
            return []
        records = []
        with open(path) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path}:{i}: {e}") from e
        return records
    return load_json(path)


def append_jsonl(path: str | Path, record: BaseModel | dict) -> None:
    line = record.model_dump_json() if isinstance(record, BaseModel) else json.dumps(record)
    with _write_lock, open(path, "a") as f:
        f.write(line + "\n")


def write_jsonl(path: str | Path, records: Iterable[BaseModel | dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write((r.model_dump_json() if isinstance(r, BaseModel) else json.dumps(r)) + "\n")


def load_models(path: str | Path, model: type[T], key: str = "case_id") -> dict[str, T]:
    """Load jsonl records keyed by `key`. Later lines win, so resumed runs can append fixes."""
    return {r[key]: model(**r) for r in read_records(path)}
