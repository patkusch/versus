PY ?= python3

.PHONY: test demo run report

test:
	PYTHONPATH=src $(PY) -m unittest discover -s tests

# no model needed: two pretend models, one strong and one weak
demo:
	PYTHONPATH=src $(PY) -m versus demo

# needs Ollama running with the model pulled; Claude column uses the `claude` command
run:
	PYTHONPATH=src $(PY) -m versus run tasks/example.jsonl --models ollama:gemma3:4b,ollama:gemma3:12b,claude:sonnet --out receipts/example.json

report:
	PYTHONPATH=src $(PY) -m versus report receipts/example.json
