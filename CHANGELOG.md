# Changelog

## 0.1.0 (2026-10-20)

- Run tasks on Ollama models and compare with Claude; answers marked by fixed rules.
- `add` brings in answers collected elsewhere; `report --rescore` re-marks saved answers.
- Cost per 1,000 tasks from `--price`; local models count as free.
- 102 example tasks across six kinds, with a real run saved in `receipts/`.
- `check` finds duplicate ids and bad rules; `run --tag` runs one kind; `report --out` saves the report.
- Clear message when Ollama is not running or the model is not pulled.
