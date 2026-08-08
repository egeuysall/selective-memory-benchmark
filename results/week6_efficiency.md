# Benchmark Cost and Time Comparison

Measured from the saved 2026-08-06 Codex CLI replay over the same 30
questions. Each condition has one observed wall-time measurement; this is not a
latency SLA or a repeated-trial estimate.

## Three-way comparison

| Approach | Prompt chars | Input proxy* | Answer chars | Output proxy* | Total proxy* | Wall time | Audited accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Large context | 34,103 | 8,526 | 2,236 | 559 | 9,085 | 150.057 s | 27/30 (90.0%) |
| Traditional TF-IDF RAG | 58,503 | 14,626 | 2,440 | 610 | 15,236 | 108.809 s | 24/30 (80.0%) |
| Selective memory | 47,380 | 11,845 | 2,556 | 639 | 12,484 | 217.326 s | 29/30 (96.7%) |

*The token proxy is `ceil(character_count / 4)`. It is a transparent size
estimate, not billable token usage. The local Codex runner did not expose an
invoice or a model price schedule, so exact USD is intentionally not asserted.

## RAG versus selective memory

| Metric | Traditional TF-IDF RAG | Selective memory | Selective-memory change vs RAG |
|---|---:|---:|---:|
| Prompt characters | 58,503 | 47,380 | -11,123 (-19.0%) |
| Estimated input tokens* | 14,626 | 11,845 | -2,781 (-19.0%) |
| Answer characters | 2,440 | 2,556 | +116 (+4.8%) |
| Estimated output tokens* | 610 | 639 | +29 (+4.8%) |
| Estimated total tokens* | 15,236 | 12,484 | -2,752 (-18.1%) |
| End-to-end wall time | 108.809 s | 217.326 s | +108.517 s (+99.7%); 2.0x slower |
| Automated correct answers | 21/30 | 25/30 | +4 answers; +13.3 percentage points |
| Audited correct answers | 24/30 | 29/30 | +5 answers; +16.7 percentage points |

The metric-specific conclusion is: selective memory was more accurate and had
a lower token-cost proxy in this replay, while traditional RAG was faster.
There is no defensible single winner without choosing an application-specific
priority or a pre-registered utility function.

## RAG retrieval coverage

The top-five RAG context contained at least one current supporting event for
28/30 questions, all supporting events for 23/30, a partial set for 5/30, and
none for 2/30. Retrieval coverage is reported separately from answer
correctness.

## Reproduce the artifacts

```bash
python3 src/week7_audit.py
python3 visual_benchmark/build_report.py
python3 visual_benchmark/build_report.py --check
```
