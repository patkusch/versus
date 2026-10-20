# Writing tasks

One task per line in a `.jsonl` file:

```json
{"id": "extract-1", "tag": "extract", "prompt": "Invoice total? Only the amount.", "check": {"type": "contains", "values": ["1,482.50"]}}
```

`tag` is the kind of task. The report groups results by it, so use 6 or more tasks per tag before reading anything into a group.

## Rules (`check`)

| type | passes when | extra fields |
|---|---|---|
| `equals` | the whole answer is this, ignoring case and end punctuation | `value` |
| `any_of` | the whole answer is one of these | `values` |
| `contains` | every one of these appears | `values` |
| `not_contains` | none of these appears | `values` |
| `regex` | the pattern matches somewhere | `pattern` |
| `number` | the last number in the answer matches | `value`, optional `tol` |
| `json` | the answer parses to exactly this JSON (a code fence is fine) | `value` |
| `max_words` | between 1 and N words | `value` |
| `word_count` | exactly N words | `value` |
| `all_caps` / `all_lower` | letters are all capitals / all lowercase | none |
| `line_count` | exactly N non-empty lines | `value` |
| `bullets` | exactly N lines, each starting `- ` | `value` |
| `all` | every rule in the list passes | `checks` |

Write prompts that ask for a short, exact answer ("reply with only the number"), so the rule has something to check.

Run `python3 -m versus check your-tasks.jsonl` before a real run.
