# Versus report

Each model answered the same 48 tasks. Every answer was checked by a fixed rule, never by another model. **claude:answered-blind** is the one we compare against.

## Overall

| Model | Got right | Share | Plausible range | Typical time per answer |
|---|---|---|---|---|
| ollama:gemma3:latest | 35 of 48 | 73% | 59% to 83% | 0.2s |
| ollama:gemma3:12b | 45 of 48 | 94% | 83% to 98% | 0.5s |
| claude:answered-blind | 48 of 48 | 100% | 93% to 100% | not measured |

*Plausible range: with this few tasks, the true score could sit anywhere in it.*

## ollama:gemma3:latest compared with claude:answered-blind

| Kind of task | Tasks | Both right | Only gemma3:latest | Only answered-blind | Neither | Verdict |
|---|---|---|---|---|---|---|
| arithmetic | 9 | 2 | 0 | 7 | 0 | keep on answered-blind |
| classify | 7 | 7 | 0 | 0 | 0 | can take this |
| extract | 8 | 7 | 0 | 1 | 0 | keep on answered-blind |
| format | 7 | 7 | 0 | 0 | 0 | can take this |
| reasoning | 9 | 6 | 0 | 3 | 0 | keep on answered-blind |
| rules | 8 | 6 | 0 | 2 | 0 | keep on answered-blind |

**ollama:gemma3:latest loses nothing on:** classify, format.
**Stay on claude:answered-blind for:** arithmetic, extract, reasoning, rules.

*"Can take this" means it got right every task the reference got right in that group. With a handful of tasks per group, treat it as a lead to test further, not a guarantee.*

## ollama:gemma3:12b compared with claude:answered-blind

| Kind of task | Tasks | Both right | Only gemma3:12b | Only answered-blind | Neither | Verdict |
|---|---|---|---|---|---|---|
| arithmetic | 9 | 6 | 0 | 3 | 0 | keep on answered-blind |
| classify | 7 | 7 | 0 | 0 | 0 | can take this |
| extract | 8 | 8 | 0 | 0 | 0 | can take this |
| format | 7 | 7 | 0 | 0 | 0 | can take this |
| reasoning | 9 | 9 | 0 | 0 | 0 | can take this |
| rules | 8 | 8 | 0 | 0 | 0 | can take this |

**ollama:gemma3:12b loses nothing on:** classify, extract, format, reasoning, rules.
**Stay on claude:answered-blind for:** arithmetic.

*"Can take this" means it got right every task the reference got right in that group. With a handful of tasks per group, treat it as a lead to test further, not a guarantee.*

## Misses

**ollama:gemma3:latest** missed 13:
- `extract-4` (extract): 11 
- `arithmetic-2` (arithmetic): 10:55 
- `arithmetic-3` (arithmetic): 52.00 
- `arithmetic-4` (arithmetic): 28.50 
- `arithmetic-5` (arithmetic): 2100 
- `arithmetic-6` (arithmetic): 600 
- `rules-5` (rules): A vast, salty ocean rolls, a constant, liquid sway.
- `reasoning-3` (reasoning): 50 
- `reasoning-5` (reasoning): 2 
- `arithmetic-8` (arithmetic): 18 
- `arithmetic-9` (arithmetic): 147.5 
- `rules-7` (rules): Crimson leaves fall gracefully, painting landscapes with autumnal beau
- `reasoning-7` (reasoning): Cara  

**ollama:gemma3:12b** missed 3:
- `arithmetic-7` (arithmetic): 40.00
- `arithmetic-8` (arithmetic): 18
- `arithmetic-9` (arithmetic): 66

**claude:answered-blind** missed 0:

