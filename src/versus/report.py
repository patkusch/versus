from __future__ import annotations

import math
import statistics
from collections import defaultdict


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% range the true pass rate could be in, given k passes out of n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def analyse(receipt: dict, reference: str | None = None) -> dict:
    models = receipt["models"]
    ref = reference or models[-1]
    tasks = {t["id"]: t for t in receipt["tasks"]}
    ok = {m: {r["id"]: r["ok"] for r in rows} for m, rows in receipt["results"].items()}

    summary = {}
    for m, rows in receipt["results"].items():
        k = sum(r["ok"] for r in rows)
        lo, hi = wilson(k, len(rows))
        secs = [r["seconds"] for r in rows if r["error"] is None]
        summary[m] = {"passed": k, "total": len(rows), "low": lo, "high": hi,
                      "median_seconds": statistics.median(secs) if secs else 0.0}

    tags = sorted({t["tag"] for t in tasks.values()})
    versus = {}
    for m in models:
        if m == ref:
            continue
        per_tag = {}
        for tag in tags:
            ids = [i for i, t in tasks.items() if t["tag"] == tag]
            both = [i for i in ids if ok[m][i] and ok[ref][i]]
            only_m = [i for i in ids if ok[m][i] and not ok[ref][i]]
            only_ref = [i for i in ids if ok[ref][i] and not ok[m][i]]
            neither = [i for i in ids if not ok[m][i] and not ok[ref][i]]
            per_tag[tag] = {"n": len(ids), "both": both, "only_candidate": only_m,
                            "only_reference": only_ref, "neither": neither,
                            "can_take": len(only_ref) == 0 and len(ids) >= 3}
        versus[m] = per_tag
    return {"reference": ref, "summary": summary, "versus": versus, "tags": tags}


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def render(receipt: dict, reference: str | None = None) -> str:
    a = analyse(receipt, reference)
    ref = a["reference"]
    out = ["# Versus report", ""]
    out.append(f"Each model answered the same {len(receipt['tasks'])} tasks. "
               f"Every answer was checked by a fixed rule, never by another model. "
               f"**{ref}** is the one we compare against.")
    out += ["", "## Overall", "",
            "| Model | Got right | Share | Plausible range | Typical time per answer |",
            "|---|---|---|---|---|"]
    for m in receipt["models"]:
        s = a["summary"][m]
        out.append(f"| {m} | {s['passed']} of {s['total']} | {pct(s['passed'] / s['total'])} | "
                   f"{pct(s['low'])} to {pct(s['high'])} | {(str(round(s['median_seconds'], 1)) + 's') if s['median_seconds'] else 'not measured'} |")
    out += ["", "*Plausible range: with this few tasks, the true score could sit anywhere in it.*"]

    for m, per_tag in a["versus"].items():
        out += ["", f"## {m} compared with {ref}", "",
                "| Kind of task | Tasks | Both right | Only " + m.split(":", 1)[1] + " | Only " + ref.split(":", 1)[1] + " | Neither | Verdict |",
                "|---|---|---|---|---|---|---|"]
        movable, kept = [], []
        for tag, d in per_tag.items():
            verdict = "can take this" if d["can_take"] else ("too few tasks to say" if d["n"] < 3 and not d["only_reference"] else "keep on " + ref.split(":", 1)[1])
            (movable if d["can_take"] else kept).append(tag)
            out.append(f"| {tag} | {d['n']} | {len(d['both'])} | {len(d['only_candidate'])} | "
                       f"{len(d['only_reference'])} | {len(d['neither'])} | {verdict} |")
        out.append("")
        if movable:
            out.append(f"**{m} loses nothing on:** {', '.join(movable)}.")
        if kept:
            out.append(f"**Stay on {ref} for:** {', '.join(kept)}.")
        out.append("")
        out.append("*\"Can take this\" means it got right every task the reference got right in that group. "
                   "With a handful of tasks per group, treat it as a lead to test further, not a guarantee.*")

    out += ["", "## Misses", ""]
    tasks = {t["id"]: t for t in receipt["tasks"]}
    for m in receipt["models"]:
        missed = [r for r in receipt["results"][m] if not r["ok"]]
        out.append(f"**{m}** missed {len(missed)}:")
        for r in missed:
            ans = (r["error"] and f"(error: {r['error'][:60]})") or r["answer"].replace("\n", " ")[:70]
            out.append(f"- `{r['id']}` ({tasks[r['id']]['tag']}): {ans}")
        out.append("")
    return "\n".join(out)
