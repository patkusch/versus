import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from versus import backends
from versus.cli import main

TASKS = [{"id": f"{tag}-{i}", "tag": tag, "prompt": f"{tag} question {i}", "check": {"type": "equals", "value": "y"}}
         for tag in ("sums", "rules") for i in range(1, 4)]


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class Commands(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.dir = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        self.tasks = self.dir / "tasks.jsonl"
        self.tasks.write_text("\n".join(json.dumps(t) for t in TASKS) + "\n")

    def pretend(self, answers_by_model):
        """Make `--models` build stand-in models that answer from a table, so nothing real is asked."""
        def make(spec):
            return backends.Pretend(spec, answers_by_model.get(spec, {}))
        return mock.patch("versus.cli.backends.make", side_effect=make)

    def test_run_asks_every_model_every_task_saves_the_answers_and_prints_the_report(self):
        everything = {t["prompt"]: "y" for t in TASKS}
        sums_only = {t["prompt"]: "y" for t in TASKS if t["tag"] == "sums"}
        out_file = self.dir / "deep" / "receipt.json"
        with self.pretend({"ollama:small": sums_only, "claude:big": everything}):
            code, out, err = call(["run", str(self.tasks), "--models", "ollama:small,claude:big", "--out", str(out_file)])
        self.assertEqual(code, 0)
        receipt = json.loads(out_file.read_text())
        self.assertEqual(receipt["models"], ["ollama:small", "claude:big"])
        self.assertEqual(sum(r["ok"] for r in receipt["results"]["ollama:small"]), 3)
        self.assertEqual(sum(r["ok"] for r in receipt["results"]["claude:big"]), 6)
        self.assertIn("# Versus report", out)
        self.assertEqual(err.count("MISS"), 3, "each missed answer is shown as it happens")
        self.assertEqual(err.count(" ok"), 9)

    def test_tag_keeps_only_those_tasks_and_an_unknown_tag_is_refused(self):
        everything = {t["prompt"]: "y" for t in TASKS}
        out_file = self.dir / "r.json"
        with self.pretend({"ollama:m": everything}):
            code, _, _ = call(["run", str(self.tasks), "--models", "ollama:m", "--out", str(out_file), "--tag", "sums"])
        self.assertEqual(code, 0)
        self.assertEqual({r["id"] for r in json.loads(out_file.read_text())["results"]["ollama:m"]}, {"sums-1", "sums-2", "sums-3"})
        with self.pretend({}):
            code, out, err = call(["run", str(self.tasks), "--models", "ollama:m", "--out", str(self.dir / "none.json"), "--tag", "nope"])
        self.assertEqual(code, 2)
        self.assertIn("versus: no tasks with tag nope", err)
        self.assertFalse((self.dir / "none.json").exists())

    def test_a_model_that_cannot_be_reached_stops_the_run_with_its_message_and_writes_nothing(self):
        class Down(backends.Backend):
            name = "ollama:x"

            def ask(self, prompt):
                raise backends.BackendUnavailable("Ollama is not running at http://127.0.0.1:11434")

        out_file = self.dir / "r.json"
        with mock.patch("versus.cli.backends.make", return_value=Down()):
            code, _, err = call(["run", str(self.tasks), "--models", "ollama:x", "--out", str(out_file)])
        self.assertEqual(code, 2)
        self.assertIn("versus: Ollama is not running", err)
        self.assertFalse(out_file.exists())

    def test_check_passes_a_clean_task_file_and_counts_the_kinds(self):
        code, out, _ = call(["check", str(self.tasks)])
        self.assertEqual(code, 0)
        self.assertIn("6 tasks, 2 kinds (rules, sums), 0 problems", out)

    def test_check_names_each_problem_and_exits_with_one(self):
        bad = self.dir / "bad.jsonl"
        bad.write_text(self.tasks.read_text() + json.dumps({"id": "sums-1", "tag": "sums", "prompt": "again", "check": {"type": "vibes"}}) + "\n")
        code, out, _ = call(["check", str(bad)])
        self.assertEqual(code, 1)
        self.assertTrue(out.count("\n") >= 3)
        self.assertIn("7 tasks, 2 kinds (rules, sums), ", out)
        self.assertNotIn(", 0 problems", out)

    def test_add_scores_answers_collected_by_hand_and_updates_the_receipt_in_place(self):
        receipt = self.dir / "r.json"
        with self.pretend({"ollama:m": {t["prompt"]: "y" for t in TASKS}}):
            call(["run", str(self.tasks), "--models", "ollama:m", "--out", str(receipt)])
        answers = self.dir / "answers.json"
        answers.write_text(json.dumps({t["id"]: "y" if t["tag"] == "sums" else "no" for t in TASKS}))
        code, out, _ = call(["add", str(receipt), "--name", "claude:by-hand", "--answers", str(answers)])
        self.assertEqual(code, 0)
        saved = json.loads(receipt.read_text())
        self.assertEqual(saved["models"], ["ollama:m", "claude:by-hand"])
        self.assertEqual(sum(r["ok"] for r in saved["results"]["claude:by-hand"]), 3)
        self.assertIn("by-hand", out)

    def test_add_refuses_a_name_that_is_not_kind_colon_model_and_leaves_the_receipt_untouched(self):
        receipt = self.dir / "r.json"
        with self.pretend({"ollama:m": {t["prompt"]: "y" for t in TASKS}}):
            call(["run", str(self.tasks), "--models", "ollama:m", "--out", str(receipt)])
        before = receipt.read_text()
        answers = self.dir / "answers.json"
        answers.write_text(json.dumps({t["id"]: "y" for t in TASKS}))
        for bad in ("by-hand", "claude:"):
            code, out, err = call(["add", str(receipt), "--name", bad, "--answers", str(answers)])
            self.assertEqual(code, 2, bad)
            self.assertIn("--name must look like ollama:<model> or claude:<model>", err)
            self.assertEqual(out, "")
        self.assertEqual(receipt.read_text(), before)

    def test_report_can_rescore_save_to_a_file_and_name_the_reference_model(self):
        receipt = self.dir / "r.json"
        with self.pretend({"ollama:a": {t["prompt"]: "y" for t in TASKS}, "claude:b": {}}):
            call(["run", str(self.tasks), "--models", "ollama:a,claude:b", "--out", str(receipt)])
        saved = json.loads(receipt.read_text())
        saved["tasks"][0]["check"] = {"type": "equals", "value": "z"}  # the answers no longer pass this one
        receipt.write_text(json.dumps(saved))
        target = self.dir / "report.md"
        code, out, _ = call(["report", str(receipt), "--rescore", "--reference", "ollama:a", "--out", str(target)])
        self.assertEqual(code, 0)
        self.assertEqual(target.read_text(), out)
        self.assertIn("# Versus report", out)

    def test_demo_runs_without_any_model(self):
        code, out, _ = call(["demo"])
        self.assertEqual(code, 0)
        self.assertIn("claude:demo", out)
        self.assertIn("ollama:demo-small", out)


if __name__ == "__main__":
    unittest.main()
