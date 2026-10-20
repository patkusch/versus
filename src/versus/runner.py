from __future__ import annotations

import json
from pathlib import Path

from .backends import Backend
from .checks import passes


def load_tasks(path: str | Path) -> list[dict]:
    tasks = []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            t = json.loads(line)
            for k in ("id", "tag", "prompt", "check"):
                if k not in t:
                    raise ValueError(f"{path}:{n}: task is missing '{k}'")
            tasks.append(t)
    return tasks


def run(tasks: list[dict], backends: list[Backend], progress=None) -> dict:
    """Ask every model every task once. Answers are kept so a check can be re-scored later."""
    results = {}
    for b in backends:
        rows = []
        for t in tasks:
            try:
                text, secs = b.ask(t["prompt"])
                error = None
            except Exception as e:  # a failed call counts as a miss, with the reason kept
                text, secs, error = "", 0.0, str(e)
            rows.append({"id": t["id"], "answer": text, "seconds": round(secs, 2),
                         "ok": error is None and passes(t["check"], text), "error": error})
            if progress:
                progress(b.name, t["id"], rows[-1]["ok"])
        results[b.name] = rows
    return {"tasks": tasks, "models": [b.name for b in backends], "results": results}


def rescore(receipt: dict) -> dict:
    """Re-apply the checks to saved answers, so fixing a check never needs a new run."""
    by_id = {t["id"]: t for t in receipt["tasks"]}
    for rows in receipt["results"].values():
        for r in rows:
            r["ok"] = r["error"] is None and passes(by_id[r["id"]]["check"], r["answer"])
    return receipt


def add_answers(receipt: dict, name: str, answers: dict[str, str]) -> dict:
    """Add a model whose answers came from somewhere else, as {task id: answer text}."""
    missing = [t["id"] for t in receipt["tasks"] if t["id"] not in answers]
    if missing:
        raise ValueError(f"answers are missing for: {', '.join(missing)}")
    if name in receipt["models"]:
        raise ValueError(f"{name} is already in the receipt")
    rows = [{"id": t["id"], "answer": answers[t["id"]], "seconds": 0.0,
             "ok": passes(t["check"], answers[t["id"]]), "error": None} for t in receipt["tasks"]]
    receipt["models"].append(name)
    receipt["results"][name] = rows
    return receipt
