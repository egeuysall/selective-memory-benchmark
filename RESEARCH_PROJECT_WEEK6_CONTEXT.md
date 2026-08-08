# Research Project - Ege: Week 6 Context

Updated: 2026-08-08

## Week 6 task

[Week 6: Design and test the selective-memory benchmark](https://app.asana.com/1/1206944340383158/project/1216398074606315/task/1216398085937096)

Status in Asana: **Complete**.

The student deliverable is to submit the revised evaluation question set,
updated scoring table, and selective-memory table. The revised benchmark must
be ready to test all three approaches: large-context prompting, RAG, and
selective memory.

## Deliverable checklist

| Required deliverable | Repository artifact | Ready |
| --- | --- | --- |
| Revised evaluation question set | `data/evaluation_questions.csv`: 30 questions with answer keys, required/forbidden keywords, and supporting/conflicting event IDs | Yes |
| Updated scoring table | `results/week6_comparison.csv` plus the three condition result CSVs | Yes |
| Selective-memory table | `data/selective_memory.csv`: current, updated, outdated, canceled, use/ignore, and source-event fields | Yes |
| Benchmark ready for all three approaches | `src/benchmark.py` and saved Week 6 raw/result files | Yes |

## What changed for Week 6

- Expanded the timeline from 86 to 90 events.
- Expanded the question set from 15 to 30 questions.
- Added repeated owner changes, multi-event reasoning, resolved and later
  blockers, canceled and revived features, similarly named tasks, successive
  deadline changes, and a future-backlog requirement.
- Added RAG retrieval scoring separately from answer scoring.
- Generated a selective-memory table with 94 rows: 22 marked `Use` and 72
  marked `Ignore`.

The four stress events are `E087` (Help Center prompt fallback revival), `E088`
(separate browser smoke-test fixtures), `E089` (outdated July 18 deadline), and
`E090` (current July 19 deadline).

## Three benchmark conditions

1. Large-context prompting receives all 90 project events.
2. Traditional TF-IDF RAG retrieves the top five events for each question.
3. Selective memory receives the generated current/history table with explicit
   `Use` and `Ignore` instructions.

All three use the same 30 questions and transparent `Correct`, `Incomplete`,
and `Incorrect` rubric.

## Latest recorded results

| Approach | Correct | Incomplete | Incorrect | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Large context | 23 | 6 | 1 | 76.7% |
| TF-IDF RAG | 21 | 8 | 1 | 70.0% |
| Selective memory | 25 | 3 | 2 | 83.3% |

RAG retrieved at least one current supporting event for 28/30 questions and
the complete supporting-event set for 23/30. An earlier live replay scored
24/30, 22/30, and 26/30; the current files reflect the newer timed replay.

## Week 7 reconciliation and analysis

The earlier 24/22/26 replay is historical only. The later 23/21/25 values are
the automated keyword labels for the saved replay. After manually reviewing
every non-Correct automated answer, the canonical publication-facing score is:

| Approach | Automated | Audited correct | Audited accuracy |
| --- | ---: | ---: | ---: |
| Large context | 23/30 | 27/30 | 90.0% |
| Traditional TF-IDF RAG | 21/30 | 24/30 | 80.0% |
| Selective memory | 25/30 | 29/30 | 96.7% |

The audited table is [`results/week7_final_scoring.csv`](results/week7_final_scoring.csv)
and the row-level review is [`results/week7_manual_review.csv`](results/week7_manual_review.csv).
Selective memory was the only highest-scoring approach on Q16, Q17, and Q25.
Its remaining miss was Q23: it cited nearby keyboard-coverage events instead
of the exact requested event pair E081 and E086. The complete analysis is in
[`results/week7_summary.md`](results/week7_summary.md).

The visual benchmark is [`visual_benchmark/benchmark.svg`](visual_benchmark/benchmark.svg).
It keeps accuracy, estimated token-cost proxy, and observed wall time as
separate metrics. Selective memory used 18.1% fewer estimated total tokens than
RAG but was 99.7% slower in this one replay; RAG was fastest. Exact USD is not
asserted because the replay did not expose billable pricing.

Week 8 manuscript writing has intentionally not started. The paper evidence
map, publication-readiness checklist, and a step-by-step writing sequence are
in [`PUBLICATION_READINESS_AND_PAPER_GUIDE.md`](PUBLICATION_READINESS_AND_PAPER_GUIDE.md).

## Validation

```text
python3 src/benchmark.py validate
Validated 90 events, 30 questions, memory rows, event references, and TF-IDF retrieval.

python3 -m unittest discover -s tests -v
Ran 4 tests: 4 passed.
```

The oracle mode was previously used as a file-generation check and scored 30/30
in all three conditions. That is a pipeline check, not the live model result.

## Supporting files

- [`data/evaluation_questions.csv`](data/evaluation_questions.csv)
- [`data/selective_memory.csv`](data/selective_memory.csv)
- [`results/week6_comparison.csv`](results/week6_comparison.csv)
- [`results/week6_large_context_results.csv`](results/week6_large_context_results.csv)
- [`results/week6_rag_results.csv`](results/week6_rag_results.csv)
- [`results/week6_selective_memory_results.csv`](results/week6_selective_memory_results.csv)
- [`results/week6_summary.md`](results/week6_summary.md)
- [`results/week6_efficiency.md`](results/week6_efficiency.md)
- [`DELIVERABLES.md`](DELIVERABLES.md)
- [`WEEK6_ASANA_SUBMISSION.md`](WEEK6_ASANA_SUBMISSION.md)
- [`results/week7_final_scoring.csv`](results/week7_final_scoring.csv)
- [`results/week7_manual_review.csv`](results/week7_manual_review.csv)
- [`results/week7_summary.md`](results/week7_summary.md)
- [`WEEK7_ASANA_SUBMISSION.md`](WEEK7_ASANA_SUBMISSION.md)
- [`PUBLICATION_READINESS_AND_PAPER_GUIDE.md`](PUBLICATION_READINESS_AND_PAPER_GUIDE.md)
