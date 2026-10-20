"""Ways to ask a model one question. Each backend is `ask(prompt) -> (text, seconds)`."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.request


class Backend:
    name = ""

    def ask(self, prompt: str) -> tuple[str, float]:
        raise NotImplementedError


class Ollama(Backend):
    def __init__(self, model: str, host: str | None = None):
        self.name = f"ollama:{model}"
        self.model = model
        self.host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        if not self.host.startswith("http"):
            self.host = "http://" + self.host

    def ask(self, prompt: str) -> tuple[str, float]:
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "seed": 7, "num_predict": 300},
        }).encode()
        req = urllib.request.Request(self.host + "/api/chat", body, {"Content-Type": "application/json"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
        return data["message"]["content"], time.time() - start


class ClaudeCli(Backend):
    """Uses the `claude` command, so it runs on your own login and needs no API key."""

    def __init__(self, model: str):
        self.name = f"claude:{model}"
        self.model = model

    def ask(self, prompt: str) -> tuple[str, float]:
        start = time.time()
        # run from an empty folder so no project notes leak into the answer
        with tempfile.TemporaryDirectory() as cwd:
            out = subprocess.run(
                ["claude", "-p", "--model", self.model, "--tools", ""],
                input=prompt, capture_output=True, text=True, cwd=cwd, timeout=300,
            )
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip() or "claude command failed")
        return out.stdout.strip(), time.time() - start


class Pretend(Backend):
    """A model that answers from a lookup table. Used by tests and the demo."""

    def __init__(self, name: str, answers: dict[str, str]):
        self.name = name
        self.answers = answers

    def ask(self, prompt: str) -> tuple[str, float]:
        return self.answers.get(prompt, "I am not sure."), 0.01


def make(spec: str) -> Backend:
    kind, _, model = spec.partition(":")
    if kind == "ollama" and model:
        return Ollama(model)
    if kind == "claude" and model:
        return ClaudeCli(model)
    raise ValueError(f"unknown model '{spec}': use ollama:<model> or claude:<model>")
