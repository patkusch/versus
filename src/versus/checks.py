"""Mechanical answer checks. No model grades another model: every task has a rule."""
from __future__ import annotations

import json
import re


def _norm(s: str) -> str:
    return re.sub(r"[^\w\s./:@-]", "", s).strip().strip(".:").strip().lower()


def _numbers(s: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"-?\d[\d,]*\.?\d*", s) if x.strip(",.")]


def _strip_fence(s: str) -> str:
    s = s.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, re.S)
    return m.group(1) if m else s


def passes(check: dict, text: str) -> bool:
    kind = check["type"]
    t = text.strip()
    if kind == "equals":
        return _norm(t) == _norm(check["value"])
    if kind == "any_of":
        return _norm(t) in {_norm(v) for v in check["values"]}
    if kind == "contains":
        return all(v.lower() in t.lower() for v in check["values"])
    if kind == "not_contains":
        return not any(v.lower() in t.lower() for v in check["values"])
    if kind == "regex":
        return re.search(check["pattern"], t, re.S) is not None
    if kind == "number":
        nums = _numbers(t)
        return bool(nums) and abs(nums[-1] - check["value"]) <= check.get("tol", 0.01)
    if kind == "json":
        try:
            return json.loads(_strip_fence(t)) == check["value"]
        except ValueError:
            return False
    if kind == "max_words":
        return 0 < len(t.split()) <= check["value"]
    if kind == "word_count":
        return len(t.split()) == check["value"]
    if kind == "all":
        return all(passes(c, text) for c in check["checks"])
    if kind == "all_caps":
        return any(c.isalpha() for c in t) and t == t.upper()
    if kind == "line_count":
        lines = [l for l in t.splitlines() if l.strip()]
        return len(lines) == check["value"]
    if kind == "bullets":
        lines = [l for l in t.splitlines() if l.strip()]
        return len(lines) == check["value"] and all(l.lstrip().startswith("- ") for l in lines)
    raise ValueError(f"unknown check type: {kind}")
