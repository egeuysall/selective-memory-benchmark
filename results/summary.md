# Benchmark Results

The large-context baseline answered 15/15 questions
correctly. The TF-IDF RAG baseline answered 15/15 correctly
with the top five retrieved updates per question.

| Approach | Correct | Incomplete | Incorrect | Accuracy |
|---|---:|---:|---:|---:|
| Large context | 15 | 0 | 0 | 100.0% |
| TF-IDF RAG | 15 | 0 | 0 | 100.0% |

The comparison tests whether smaller retrieved contexts reduce conflict or
instead omit the newer event needed to replace an older fact. Automated labels
use a transparent keyword rubric and should be reviewed alongside the saved
answers before drawing conclusions.
