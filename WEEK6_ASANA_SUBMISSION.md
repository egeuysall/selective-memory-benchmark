# Week 6 Asana Submission

This packet verifies that the Week 6 student deliverable is complete and gives
the exact comment text for Asana.

## Student deliverable verification

The revised benchmark includes all three required submission artifacts:

- **Revised evaluation question set:** `data/evaluation_questions.csv`, with 30
  harder questions, answer keys, required/forbidden keywords, and supporting or
  conflicting event IDs.
- **Updated scoring table:** `results/week6_comparison.csv`, plus separate
  large-context, RAG, and selective-memory result tables. RAG records retrieval
  coverage separately from answer correctness.
- **Selective-memory table:** `data/selective_memory.csv`, with 94 rows and
  columns for current status, original information, updated information,
  use/ignore decision, notes, and supporting event IDs.

The benchmark is runnable for large-context prompting, traditional TF-IDF RAG,
and selective memory using the same 30 questions.

## Current results

| Approach | Correct | Incomplete | Incorrect | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Large context | 23 | 6 | 1 | 76.7% |
| Traditional TF-IDF RAG | 21 | 8 | 1 | 70.0% |
| Selective memory | 25 | 3 | 2 | 83.3% |

RAG top-five retrieval contained at least one current supporting event for
28/30 questions and the complete supporting set for 23/30.

## Copy-ready Asana comment

```text
Week 6 student deliverable complete.

I submitted the revised evaluation question set, updated scoring table, and
selective-memory table in the public repository:
https://github.com/egeuysall/selective-memory-benchmark

Deliverables:
- data/evaluation_questions.csv: 30-question revised benchmark with answer
  keys, required/forbidden keywords, and supporting/conflicting event IDs.
- results/week6_comparison.csv: updated scoring table comparing large-context
  prompting, traditional TF-IDF RAG, and selective memory.
- data/selective_memory.csv: 94-row memory table with current, updated,
  outdated, canceled, Use/Ignore, notes, and supporting event ID fields.

The revised benchmark is ready to test all three approaches using the same
questions. It includes repeated owner changes, resolved and later blockers,
canceled/revived features, similarly named tasks, successive deadline changes,
and outdated-information cases. RAG retrieval success is scored separately
from answer success.

Latest live replay: large context 23/30 (76.7%), RAG 21/30 (70.0%), and
selective memory 25/30 (83.3%). RAG retrieved at least one current supporting
event for 28/30 questions and the complete supporting set for 23/30.

Validation passed: 90 events, 30 questions, source-event references, selective
memory generation, and 4/4 unit tests.
```

## Reproduce the checks

```bash
python3 src/benchmark.py validate
python3 -m unittest discover -s tests -v
python3 src/benchmark.py run --mode all --engine oracle --top-k 5
```
