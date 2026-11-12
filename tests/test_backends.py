import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from versus import backends


class Fake(BaseHTTPRequestHandler):
    """A tiny stand-in for the Ollama server so the real request code runs."""

    seen = []
    status = 200

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.seen.append((self.path, body))
        self.send_response(Fake.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if Fake.status == 200:
            self.wfile.write(json.dumps({
                "message": {"content": "42"}, "prompt_eval_count": 11, "eval_count": 3,
            }).encode())
        else:
            self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


class OllamaBackend(unittest.TestCase):
    def setUp(self):
        Fake.seen, Fake.status = [], 200
        self.server = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.host = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_asks_the_chat_endpoint_and_records_token_counts(self):
        b = backends.Ollama("gemma3:4b", host=self.host)
        text, seconds = b.ask("what is 6 x 7?")
        self.assertEqual(text, "42")
        self.assertGreaterEqual(seconds, 0)
        self.assertEqual(b.tokens, (11, 3))
        path, body = Fake.seen[0]
        self.assertEqual(path, "/api/chat")
        self.assertEqual(body["model"], "gemma3:4b")
        self.assertEqual(body["messages"], [{"role": "user", "content": "what is 6 x 7?"}])
        self.assertIs(body["stream"], False)

    def test_answers_are_repeatable_because_temperature_is_zero_and_seed_fixed(self):
        backends.Ollama("m", host=self.host).ask("x")
        opts = Fake.seen[0][1]["options"]
        self.assertEqual(opts["temperature"], 0)
        self.assertEqual(opts["seed"], 7)

    def test_missing_model_says_how_to_fetch_it(self):
        Fake.status = 404
        with self.assertRaises(backends.BackendUnavailable) as cm:
            backends.Ollama("nope:1b", host=self.host).ask("x")
        self.assertIn("ollama pull nope:1b", str(cm.exception))

    def test_other_server_errors_are_not_called_unavailable(self):
        Fake.status = 500
        with self.assertRaises(Exception) as cm:
            backends.Ollama("m", host=self.host).ask("x")
        self.assertNotIsInstance(cm.exception, backends.BackendUnavailable)

    def test_nothing_listening_says_how_to_start_it(self):
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(backends.BackendUnavailable) as cm:
            backends.Ollama("m", host=self.host).ask("x")
        self.assertIn("ollama serve", str(cm.exception))
        self.server = HTTPServer(("127.0.0.1", 0), Fake)  # so tearDown has something to close
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


class Setup(unittest.TestCase):
    def test_host_gets_http_added_and_comes_from_the_environment(self):
        self.assertEqual(backends.Ollama("m", host="box:1234").host, "http://box:1234")
        with mock.patch.dict("os.environ", {"OLLAMA_HOST": "10.0.0.5:11434"}):
            self.assertEqual(backends.Ollama("m").host, "http://10.0.0.5:11434")
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(backends.Ollama("m").host, "http://127.0.0.1:11434")

    def test_make_builds_the_right_backend_and_names_it(self):
        self.assertEqual(backends.make("ollama:gemma3:4b").name, "ollama:gemma3:4b")
        self.assertEqual(backends.make("claude:haiku").name, "claude:haiku")
        with self.assertRaises(ValueError):
            backends.make("ollama:")
        with self.assertRaises(ValueError):
            backends.make("nonsense")

    def test_pretend_answers_from_its_table_and_admits_when_it_does_not_know(self):
        b = backends.Pretend("p", {"q": "a"})
        self.assertEqual(b.ask("q")[0], "a")
        self.assertEqual(b.ask("other")[0], "I am not sure.")


class ClaudeCli(unittest.TestCase):
    def test_runs_the_claude_command_from_an_empty_folder_with_no_tools(self):
        done = mock.Mock(returncode=0, stdout="  answer \n", stderr="")
        with mock.patch("subprocess.run", return_value=done) as run:
            text, _ = backends.ClaudeCli("haiku").ask("hi")
        self.assertEqual(text, "answer")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["claude", "-p", "--model", "haiku", "--tools", ""])
        self.assertEqual(kwargs["input"], "hi")

    def test_failure_carries_the_error_text(self):
        done = mock.Mock(returncode=1, stdout="", stderr="not logged in")
        with mock.patch("subprocess.run", return_value=done):
            with self.assertRaisesRegex(RuntimeError, "not logged in"):
                backends.ClaudeCli("haiku").ask("hi")


if __name__ == "__main__":
    unittest.main()
