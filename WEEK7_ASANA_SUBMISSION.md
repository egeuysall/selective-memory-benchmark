# Week 7 Asana Submission

Task: [Week 7: Score responses and analyze performance](https://app.asana.com/1/1206944340383158/project/1216398074606315/task/1216398085937099)

## Copy-ready Asana comment

```text
Week 7 scoring and analysis complete.

I reconciled the earlier 24/22/26 replay with the later 23/21/25 automated
replay. The 24/22/26 set is historical only. The publication-facing score is
the manual audit of the saved 23/21/25 replay:

- Large context: 27/30 correct (90.0%); automated rubric 23/30.
- Traditional TF-IDF RAG: 24/30 correct (80.0%); automated rubric 21/30.
- Selective memory: 29/30 correct (96.7%); automated rubric 25/30.

The complete audited scoring table is results/week7_final_scoring.csv. The
manual review of every non-Correct automated response is in
results/week7_manual_review.csv, with the answer, expected answer, source
event IDs, manual label, error category, and review reason.

Selective memory was the only highest-scoring approach on Q16 (repeated owner
changes), Q17 (resolved blocker followed by a later blocker), and Q25 (canceled
features). Its remaining miss was Q23: the answer cited nearby keyboard-
coverage events instead of the exact requested event pair E081 and E086.

The summary figures are in visual_benchmark/index.html. They include audited
and automated accuracy, outcome mix, audited error categories, and RAG
retrieval coverage. RAG retrieved at least one current supporting event for
28/30 questions, all supporting events for 23/30, a partial set for 5/30, and
none for 2/30.

Efficiency is reported without bias or a composite score. Estimated total
token proxy / observed wall time were: large context 9,085 / 150.057s,
traditional RAG 15,236 / 108.809s, and selective memory 12,484 / 217.326s.
Selective memory used 18.1% fewer estimated total tokens than RAG but was
99.7% slower in this one replay; RAG was fastest. Exact USD is not claimed
because the Codex run did not expose billable pricing or invoice-level usage.

The public repository contains the revised question set, scoring tables,
selective-memory table, audit, summary, and visual benchmark:
https://github.com/egeuysall/selective-memory-benchmark

Validation passed:
python3 src/benchmark.py validate
python3 -m unittest discover -s tests -v
python3 src/week7_audit.py
python3 visual_benchmark/build_report.py --check

Week 8 manuscript writing has not been started. A separate writing roadmap
and publication-readiness checklist is in
PUBLICATION_READINESS_AND_PAPER_GUIDE.md.
```

## Submission files

- `results/week7_final_scoring.csv` — all 90 approach/question scoring rows.
- `results/week7_manual_review.csv` — the 21 saved non-Correct automated rows
  with manual labels and reasons.
- `results/week7_summary.md` — reconciled final results, error categories,
  selective-memory wins, and the Q23 failure.
- `visual_benchmark/index.html` — accuracy, outcome, error, retrieval, cost,
  time, and question-level figures.
- `PUBLICATION_READINESS_AND_PAPER_GUIDE.md` — paper evidence map and writing
  sequence; Week 8 remains unstarted.
