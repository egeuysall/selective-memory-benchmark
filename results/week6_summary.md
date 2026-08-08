# RecallBench Results

The large-context baseline answered 23/30 questions
correctly. The TF-IDF RAG baseline answered 21/30 correctly
with the top five retrieved updates per question. Selective memory answered
25/30 correctly from the generated memory
table.

The top-five retrieval contained at least one supporting event for 28/30 questions and the full supporting event set for 23/30. RAG answer correctness is scored separately from retrieval coverage.

| Approach | Correct | Incomplete | Incorrect | Accuracy |
|---|---:|---:|---:|---:|
| Large context | 23 | 6 | 1 | 76.7% |
| TF-IDF RAG | 21 | 8 | 1 | 70.0% |
| Selective memory | 25 | 3 | 2 | 83.3% |

The comparison tests whether smaller retrieved contexts reduce conflict or
instead omit the newer event needed to replace an older fact. Automated labels
use a transparent keyword rubric and should be reviewed alongside the saved
answers before drawing conclusions.

The publication-facing Week 7 audit of this saved replay is in
[`week7_final_scoring.csv`](week7_final_scoring.csv) and
[`week7_summary.md`](week7_summary.md). It reports audited scores of 27/30
for large context, 24/30 for traditional TF-IDF RAG, and 29/30 for selective
memory while preserving the automated labels above for auditability.
