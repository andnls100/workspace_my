"""Shared helpers for the contract-review distillation pipeline."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DISTILL = ROOT / "distill"
DATA = Path(os.getenv("DISTILL_OUTPUT_DIR", str(DISTILL / "data")))

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
            else:
                print(f"[跳过] {path}:{n} 不是 JSON 对象")
        except json.JSONDecodeError as exc:
            print(f"[跳过] {path}:{n} JSON 无效: {exc}")
    return rows

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
