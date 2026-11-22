# Working in versus

Which of your tasks can a free model on your laptop do, and which still need Claude?

## Run the tests

You need Python 3.11 or newer.

```bash
make test
```

Every test should pass before you start and after you finish.

## Where things are

- `src/`: the code
- `tests/`: the tests
- `docs/`: written documentation
- `scripts/`: helper scripts, not part of the tool itself
- `receipts/`: saved results of earlier runs
- `tasks/`: the task files it runs

## Before you commit

- Make sure the tests pass.
- Put changes people will notice in `CHANGELOG.md`.
- Do not put real passwords, keys or private data in test files or examples. Use made-up ones.
