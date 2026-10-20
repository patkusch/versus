<h1 align="center">versus</h1>
<p align="center">Which of your tasks can a free model on your laptop do, and which still need Claude?</p>

**Run your own tasks on a local open model and on Claude, side by side.**
**It tells you which kinds of task the cheap one handles, and where it lets you down.**

## The thirty-second version

The "open or closed models" argument usually stays an argument. This turns it into a table you can read.

I ran 48 small everyday tasks (pull a number out of text, do a word problem, follow a formatting rule, spot sarcasm) on two free models on a laptop and on Claude. A fixed rule marked every answer right or wrong. No model marked another model.

| Model | Got right | Share |
|---|---|---|
| Gemma 3, 4B (small, free) | 35 of 48 | 73% |
| Gemma 3, 12B (bigger, free) | 45 of 48 | 94% |
| Claude | 48 of 48 | 100% |

The useful part is where the misses fall:

- **The small model handled all of the labelling and formatting tasks** (7 of 7 each) and missed 7 of 9 word problems. For those jobs it is free and fast.
- **The bigger free model matched Claude on everything except arithmetic**, where it missed 3 of 9. It said 66 for "15% of 240 plus 35% of 80". The answer is 64.
- **The small model wrote "A vast, salty ocean rolls, a constant, liquid sway"** when asked for a sentence with no letter "e". It cannot follow a rule it cannot check.

So the answer is not "open or closed". It is: send labelling and formatting to the free model, and keep the maths on Claude.

## How big a claim is this?

Small. 48 tasks, 6 to 9 per kind. The table above shows a range next to every score for this reason: 94% on 48 tasks could really be anywhere from 83% to 98%. "Can take this" in the report means "got right everything Claude got right", which is a lead worth testing on more tasks of your own, not a guarantee.

The Claude answers came from a Claude agent given only the questions, with no tools and no sight of the answer rules. Its time is not measured. Answers from the two Gemma models were collected at temperature 0 through a local Ollama.

## Use it on your own tasks

Write your tasks as one line each, with a rule that decides right or wrong:

```json
{"id": "extract-1", "tag": "extract", "prompt": "Invoice total? Only the amount.", "check": {"type": "contains", "values": ["1,482.50"]}}
```

Rules available: `equals`, `any_of`, `contains`, `not_contains`, `regex`, `number`, `json`, `max_words`, `word_count`, `all_caps`, `line_count`, `bullets`, and `all` (several rules at once). The tasks I used are in [`tasks/example.jsonl`](tasks/example.jsonl).

```bash
make demo        # no model needed: two pretend models
make test        # 18 tests

# real run: needs Ollama running with the models pulled
PYTHONPATH=src python3 -m versus run tasks/example.jsonl \
  --models ollama:gemma3:4b,ollama:gemma3:12b,claude:sonnet --out receipts/mine.json

# bring answers you collected yourself (a JSON file of task id -> answer)
PYTHONPATH=src python3 -m versus add receipts/mine.json --name claude:other --answers answers.json

# re-mark saved answers after fixing a rule, with no new model calls
PYTHONPATH=src python3 -m versus report receipts/mine.json --rescore
```

The last model in `--models` is the one the others are compared with. The `claude:` option runs the `claude` command on your own login, so it needs no key. Zero dependencies, Python 3.11 or newer.

The full output of the run above is in [`receipts/REPORT.md`](receipts/REPORT.md), with every saved answer in `receipts/gemma.json`.

## Not done yet

- More tasks per kind. Nine is a start, not a verdict.
- Cost per task, so "the free model can take it" comes with a saving attached.
- Repeat runs at a warmer temperature, to see how steady each model is.

MIT licence.
