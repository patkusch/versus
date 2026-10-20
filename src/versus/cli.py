from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import backends, report, runner


def _demo() -> int:
    tasks = [
        {"id": f"{tag}-{i}", "tag": tag, "prompt": f"{tag} question {i}", "check": {"type": "equals", "value": "right"}}
        for tag in ("sums", "lookups", "rules") for i in range(1, 5)
    ]
    strong = backends.Pretend("claude:demo", {t["prompt"]: "right" for t in tasks})
    weak_right = {t["prompt"]: "right" for t in tasks if not t["id"].startswith("rules") and t["id"] != "sums-4"}
    weak = backends.Pretend("ollama:demo-small", weak_right)
    receipt = runner.run(tasks, [weak, strong])
    print(report.render(receipt))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="versus", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="ask every model every task and save the answers")
    r.add_argument("tasks")
    r.add_argument("--models", required=True, help="comma list, e.g. ollama:gemma3:4b,claude:sonnet (last is the reference)")
    r.add_argument("--out", required=True)
    r.add_argument("--tag", action="append", help="only run tasks of this kind (repeatable)")
    r.add_argument("--price", action="append", help="model=input,output dollars per million tokens, e.g. claude:sonnet=2,10")
    g = sub.add_parser("report", help="turn saved answers into a plain-English report")
    g.add_argument("receipt")
    g.add_argument("--reference")
    g.add_argument("--price", action="append", help="model=input,output dollars per million tokens, e.g. claude:sonnet=2,10")
    g.add_argument("--out", help="also save the report to this file")
    g.add_argument("--rescore", action="store_true", help="re-apply the task checks to the saved answers first")
    a = sub.add_parser("add", help="add a model whose answers you collected yourself (a JSON file of id -> answer)")
    a.add_argument("receipt")
    a.add_argument("--name", required=True)
    a.add_argument("--answers", required=True)
    a.add_argument("--price", action="append", help="model=input,output dollars per million tokens")
    c = sub.add_parser("check", help="look for mistakes in a task file before spending time on a run")
    c.add_argument("tasks")
    sub.add_parser("demo", help="no model needed: two pretend models")
    args = p.parse_args(argv)

    if args.cmd == "demo":
        return _demo()
    if args.cmd == "check":
        tasks = runner.load_tasks(args.tasks)
        bad = runner.problems(tasks)
        for line in bad:
            print(line)
        kinds = sorted({t["tag"] for t in tasks})
        print(f"{len(tasks)} tasks, {len(kinds)} kinds ({', '.join(kinds)}), {len(bad)} problems")
        return 1 if bad else 0
    if args.cmd == "run":
        tasks = runner.load_tasks(args.tasks)
        if args.tag:
            tasks = [t for t in tasks if t["tag"] in args.tag]
            if not tasks:
                print(f"versus: no tasks with tag {', '.join(args.tag)}", file=sys.stderr)
                return 2
        bs = [backends.make(s) for s in args.models.split(",")]
        try:
            receipt = runner.run(tasks, bs, progress=lambda m, i, ok: print(f"{m:24} {i:18} {'ok' if ok else 'MISS'}", file=sys.stderr))
        except backends.BackendUnavailable as e:
            print(f"versus: {e}", file=sys.stderr)
            return 2
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(receipt, indent=1))
        print(report.render(receipt, prices=report.parse_prices(args.price)))
        return 0
    receipt = json.loads(Path(args.receipt).read_text())
    if args.cmd == "add":
        runner.add_answers(receipt, args.name, json.loads(Path(args.answers).read_text()))
        Path(args.receipt).write_text(json.dumps(receipt, indent=1))
        print(report.render(receipt, prices=report.parse_prices(args.price)))
        return 0
    if args.rescore:
        receipt = runner.rescore(receipt)
    text = report.render(receipt, args.reference, report.parse_prices(args.price))
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0
