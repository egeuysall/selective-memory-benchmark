# Week 7 Scoring and Analysis

This is the publication-facing score for the saved Week 6 live replay.
The original automated keyword labels remain in the Week 6 CSVs; this
audited table records the manual adjudication of every non-Correct row.
The headline score counts only `Correct` as correct and does not combine
accuracy, token cost, or time into a subjective composite.

## Final audited result

| Approach | Correct | Partially correct | Incorrect | Accuracy |
|---|---:|---:|---:|---:|
| Large context | 27 | 2 | 1 | 90.0% |
| Traditional TF-IDF RAG | 24 | 5 | 1 | 80.0% |
| Selective memory | 29 | 0 | 1 | 96.7% |

The reconciled final manuscript numbers are therefore **large context
27/30 (90.0%)**, **traditional TF-IDF RAG 24/30 (80.0%)**, and
**selective memory 29/30 (96.7%)**. The older 24/22/26 replay is
historical only; the automated labels for the current replay are retained
as 23/21/25 for auditability.

## Automated versus audited labels

| Approach | Automated correct | Audited correct | Rows promoted after review |
|---|---:|---:|---:|
| Large context | 23/30 | 27/30 | 4 |
| Traditional TF-IDF RAG | 21/30 | 24/30 | 3 |
| Selective memory | 25/30 | 29/30 | 4 |

Promotions are wording-level false negatives or semantically complete
answers identified during the manual audit; they are not hidden changes
to the saved model answers.

## Where selective memory helped

Selective memory was the only approach with the highest audited label on:

- `Q16`
- `Q17`
- `Q25`

These are the examples to inspect in the Results and Discussion sections.

## Selective-memory failure

| Question | Audited label | Cause |
|---|---|---|
| `Q23` | Incorrect | Event provenance: The question asks for E081 and E086, but the answer cites E084, E085, E089, and E090 instead. |

The selective-memory miss is an event-provenance error: the answer
described nearby keyboard-coverage changes but did not cite the two
events requested by the question (E081 and E086).

## Audited error categories

| Error category | Large context | Traditional TF-IDF RAG | Selective memory |
|---|---:|---:|---:|
| Canceled/obsolete scope | 1 | 1 | 0 |
| Event provenance | 0 | 0 | 1 |
| Irrelevant-information overinclusion | 0 | 1 | 0 |
| Missed QA rule detail | 0 | 1 | 0 |
| Missed blocker transition | 1 | 1 | 0 |
| Missed recovery requirement detail | 0 | 1 | 0 |
| Multi-owner history | 1 | 1 | 0 |

## RAG retrieval coverage

The top-five RAG context retrieved at least one supporting current event
for 28/30 questions, all supporting events for 23/30, a partial set for
5/30, and none for 2/30. Retrieval coverage and answer correctness remain
separate measures.

## Reproduce

```bash
python3 src/week7_audit.py
python3 visual_benchmark/build_report.py --check
```

The visual benchmark is [the Vercel-style SVG](../visual_benchmark/benchmark.svg).
Its price comparison is an estimated token-cost proxy because the Codex
replay did not expose billable USD or a model price schedule.

Independent human sign-off is still required before manuscript submission
because this audit is a single reviewer pass over one stochastic replay.
