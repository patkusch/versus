# Versus report

Each model answered the same 102 tasks. Every answer was checked by a fixed rule, never by another model. **claude:answered-blind** is the one we compare against.

## Overall

| Model | Got right | Share | Plausible range | Typical time per answer | Cost for 1,000 tasks |
|---|---|---|---|---|---|
| ollama:gemma3:latest | 84 of 102 | 82% | 74% to 89% | 0.2s | $0.00 |
| ollama:gemma3:12b | 97 of 102 | 95% | 89% to 98% | 0.5s | $0.00 |
| claude:answered-blind | 102 of 102 | 100% | 96% to 100% | not measured | $0.09 |

*Plausible range: with this few tasks, the true score could sit anywhere in it.*
*Cost counts the words sent and received at the price you gave. Local models cost nothing per use, but the electricity and the laptop are yours. Token counts are exact for Ollama and a rough guess (4 characters a token) for answers brought in from elsewhere.*

## ollama:gemma3:latest compared with claude:answered-blind

| Kind of task | Tasks | Both right | Only gemma3:latest | Only answered-blind | Neither | Verdict |
|---|---|---|---|---|---|---|
| arithmetic | 18 | 9 | 0 | 9 | 0 | keep on answered-blind |
| classify | 16 | 16 | 0 | 0 | 0 | can take this |
| extract | 17 | 16 | 0 | 1 | 0 | keep on answered-blind |
| format | 16 | 15 | 0 | 1 | 0 | keep on answered-blind |
| reasoning | 18 | 14 | 0 | 4 | 0 | keep on answered-blind |
| rules | 17 | 14 | 0 | 3 | 0 | keep on answered-blind |

**ollama:gemma3:latest loses nothing on:** classify.
**Stay on claude:answered-blind for:** arithmetic, extract, format, reasoning, rules.

*"Can take this" means it got right every task the reference got right in that group. With a handful of tasks per group, treat it as a lead to test further, not a guarantee.*

## ollama:gemma3:12b compared with claude:answered-blind

| Kind of task | Tasks | Both right | Only gemma3:12b | Only answered-blind | Neither | Verdict |
|---|---|---|---|---|---|---|
| arithmetic | 18 | 15 | 0 | 3 | 0 | keep on answered-blind |
| classify | 16 | 16 | 0 | 0 | 0 | can take this |
| extract | 17 | 16 | 0 | 1 | 0 | keep on answered-blind |
| format | 16 | 16 | 0 | 0 | 0 | can take this |
| reasoning | 18 | 17 | 0 | 1 | 0 | keep on answered-blind |
| rules | 17 | 17 | 0 | 0 | 0 | can take this |

**ollama:gemma3:12b loses nothing on:** classify, format, rules.
**Stay on claude:answered-blind for:** arithmetic, extract, reasoning.

*"Can take this" means it got right every task the reference got right in that group. With a handful of tasks per group, treat it as a lead to test further, not a guarantee.*

## Misses

**ollama:gemma3:latest** missed 18:
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
- `arithmetic-10` (arithmetic): 20 
- `arithmetic-16` (arithmetic): 6.50 
- `format-11` (format): meerts 
- `rules-13` (rules): The silver orb hangs in the night sky, silent.
- `reasoning-14` (reasoning): West

**ollama:gemma3:12b** missed 5:
- `arithmetic-7` (arithmetic): 40.00
- `arithmetic-8` (arithmetic): 18
- `arithmetic-9` (arithmetic): 66
- `extract-14` (extract): 356
- `reasoning-18` (reasoning): Friday

**claude:answered-blind** missed 0:

