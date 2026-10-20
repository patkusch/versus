import json
import tempfile
import unittest
from pathlib import Path

from versus import backends, checks, report, runner
from versus.cli import main


class Checks(unittest.TestCase):
    def test_number_takes_last_number_and_commas(self):
        self.assertTrue(checks.passes({"type": "number", "value": 12600}, "It is 12,600 seconds"))
        self.assertTrue(checks.passes({"type": "number", "value": 5}, "3 + 2 = 5"))
        self.assertFalse(checks.passes({"type": "number", "value": 5}, "no idea"))

    def test_equals_ignores_case_and_punctuation_but_not_extra_words(self):
        c = {"type": "equals", "value": "spam"}
        self.assertTrue(checks.passes(c, "Spam."))
        self.assertFalse(checks.passes(c, "not spam"))

    def test_json_accepts_code_fence(self):
        c = {"type": "json", "value": ["a"]}
        self.assertTrue(checks.passes(c, '```json\n["a"]\n```'))
        self.assertFalse(checks.passes(c, "[a]"))

    def test_rules(self):
        self.assertTrue(checks.passes({"type": "bullets", "value": 2}, "- a\n- b"))
        self.assertFalse(checks.passes({"type": "bullets", "value": 2}, "1. a\n2. b"))
        self.assertTrue(checks.passes({"type": "all_caps"}, "HELLO, GOODBYE"))
        self.assertFalse(checks.passes({"type": "all_caps"}, "Hello"))
        self.assertTrue(checks.passes({"type": "max_words", "value": 3}, "one two three"))
        self.assertFalse(checks.passes({"type": "not_contains", "values": ["e"]}, "The sea"))

    def test_word_count_and_combined_checks(self):
        self.assertTrue(checks.passes({"type": "word_count", "value": 3}, "one two three"))
        self.assertFalse(checks.passes({"type": "word_count", "value": 3}, "one two"))
        both = {"type": "all", "checks": [{"type": "line_count", "value": 2}, {"type": "all_caps"}]}
        self.assertTrue(checks.passes(both, "FRANCE\nSPAIN"))
        self.assertFalse(checks.passes(both, "FRANCE\nSpain"))

    def test_unknown_check_is_an_error(self):
        with self.assertRaises(ValueError):
            checks.passes({"type": "vibes"}, "x")


def tasks():
    return [{"id": f"{tag}-{i}", "tag": tag, "prompt": f"{tag}{i}", "check": {"type": "equals", "value": "y"}}
            for tag in ("a", "b") for i in range(3)]


class Runner(unittest.TestCase):
    def test_failed_call_counts_as_miss_and_keeps_reason(self):
        class Broken(backends.Backend):
            name = "broken"

            def ask(self, prompt):
                raise RuntimeError("server down")

        rc = runner.run(tasks(), [Broken()])
        row = rc["results"]["broken"][0]
        self.assertFalse(row["ok"])
        self.assertEqual(row["error"], "server down")

    def test_rescore_fixes_a_wrong_check_without_new_answers(self):
        t = tasks()
        rc = runner.run(t, [backends.Pretend("m", {x["prompt"]: "Y!" for x in t})])
        self.assertEqual(sum(r["ok"] for r in rc["results"]["m"]), 6)  # equals ignores case and punctuation
        rc["tasks"][0]["check"] = {"type": "equals", "value": "z"}
        runner.rescore(rc)
        self.assertEqual(sum(r["ok"] for r in rc["results"]["m"]), 5)

    def test_add_answers_scores_them_and_refuses_gaps(self):
        t = tasks()
        rc = runner.run(t, [backends.Pretend("m", {})])
        runner.add_answers(rc, "other", {x["id"]: "y" for x in t})
        self.assertEqual(rc["models"], ["m", "other"])
        self.assertTrue(all(r["ok"] for r in rc["results"]["other"]))
        with self.assertRaises(ValueError):
            runner.add_answers(rc, "third", {"a-0": "y"})
        with self.assertRaises(ValueError):
            runner.add_answers(rc, "other", {x["id"]: "y" for x in t})

    def test_bad_model_spec(self):
        with self.assertRaises(ValueError):
            backends.make("gpt:4")

    def test_task_file_missing_field(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.jsonl"
            p.write_text('{"id":"x"}\n')
            with self.assertRaises(ValueError):
                runner.load_tasks(p)

    def test_shipped_tasks_load_and_have_known_checks(self):
        ts = runner.load_tasks(Path(__file__).parent.parent / "tasks" / "example.jsonl")
        self.assertEqual(len(ts), 48)
        self.assertEqual(len({t["id"] for t in ts}), 48)
        for t in ts:
            checks.passes(t["check"], "x")  # raises on an unknown type


class Report(unittest.TestCase):
    def make(self, weak_misses):
        t = tasks()
        strong = backends.Pretend("claude:big", {x["prompt"]: "y" for x in t})
        weak = backends.Pretend("ollama:small", {x["prompt"]: "y" for x in t if x["id"] not in weak_misses})
        return runner.run(t, [weak, strong])

    def test_group_with_no_loss_can_move(self):
        a = report.analyse(self.make({"b-0", "b-1"}))
        v = a["versus"]["ollama:small"]
        self.assertTrue(v["a"]["can_take"])
        self.assertFalse(v["b"]["can_take"])
        self.assertEqual(v["b"]["only_reference"], ["b-0", "b-1"])

    def test_candidate_beating_reference_is_not_a_loss(self):
        t = tasks()
        weak = backends.Pretend("ollama:small", {x["prompt"]: "y" for x in t})
        strong = backends.Pretend("claude:big", {x["prompt"]: "y" for x in t if x["id"] != "a-0"})
        v = report.analyse(runner.run(t, [weak, strong]))["versus"]["ollama:small"]
        self.assertTrue(v["a"]["can_take"])
        self.assertEqual(v["a"]["only_candidate"], ["a-0"])

    def test_small_group_is_never_called_safe(self):
        t = tasks()[:1] + tasks()[3:]
        rc = runner.run(t, [backends.Pretend("o:s", {x["prompt"]: "y" for x in t}),
                            backends.Pretend("c:b", {x["prompt"]: "y" for x in t})])
        self.assertFalse(report.analyse(rc)["versus"]["o:s"]["a"]["can_take"])

    def test_wilson_range_is_wide_for_few_tasks(self):
        lo, hi = report.wilson(6, 6)
        self.assertLess(lo, 0.65)
        self.assertAlmostEqual(hi, 1.0)
        self.assertEqual(report.wilson(0, 0), (0.0, 0.0))

    def test_render_names_what_to_keep(self):
        text = report.render(self.make({"b-0"}))
        self.assertIn("loses nothing on:** a", text)
        self.assertIn("Stay on claude:big for:** b", text)

    def test_cli_demo_and_report_roundtrip(self):
        self.assertEqual(main(["demo"]), 0)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.json"
            p.write_text(json.dumps(self.make({"b-0"})))
            self.assertEqual(main(["report", str(p), "--rescore"]), 0)


if __name__ == "__main__":
    unittest.main()
