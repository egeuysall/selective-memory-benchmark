# RecallBench

**Evaluating AI Memory for Long-Term Project Support**

RecallBench contains the Week 4–6 experiments for the research project
originally proposed as *Selective Memory in AI Agents: A Benchmark for
Long-Term Project Support*. It compares:

1. a large-context baseline that receives all project updates; and
2. a simple RAG baseline that receives the five highest-scoring TF-IDF updates
   for each question; and
3. a selective-memory condition generated from current, updated, outdated, and
   canceled facts with explicit use/ignore labels.

The original benchmark uses 15 questions. The Week 6 revision uses 30 questions
and 90 events about current owners, completed and delayed
tasks, blockers, changed requirements, canceled work, and conflicts between old
and new facts. The fictional ShieldPath Learning Lab timeline was inspired by
activity from a real student software project and transformed into a fictional
benchmark.

## Data

- [Public Week 3 Google Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vShzbDGNay0SFVU8jsFeOO9Xr_NNcNiKUxvRHrRnYnJBZkybYBQs2o0X3mJe8akU0riTyxe6lF2_Exh/pubhtml)
- `data/project_updates.csv`: the 90-event Week 6 timeline (86 original events plus four stress events)
- `data/day30_current_state.csv`: the final selective-memory state
- `data/evaluation_questions.csv`: the 30-question Week 6 rubric and source-event map
- `data/selective_memory.csv`: generated selective-memory table

No private project data, credentials, or contact details are included.

## Submission

- [Complete Week 4–6 deliverables](DELIVERABLES.md)
- [Public Week 3 Google Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vShzbDGNay0SFVU8jsFeOO9Xr_NNcNiKUxvRHrRnYnJBZkybYBQs2o0X3mJe8akU0riTyxe6lF2_Exh/pubhtml)
- [Week 6 context and task record](RESEARCH_PROJECT_WEEK6_CONTEXT.md)
- [Recorded Week 6 comparison results](results/week6_summary.md)
- [Week 6 Asana submission packet](WEEK6_ASANA_SUBMISSION.md)
- [Week 6 efficiency comparison](results/week6_efficiency.md)

## Run locally

Requirements: Python 3.11 or newer and an authenticated
[Codex CLI](https://developers.openai.com/codex/cli).

```bash
python3 src/benchmark.py validate
python3 -m unittest discover -s tests -v
python3 src/benchmark.py run --mode all --engine codex --top-k 5
```

The final command makes three model calls: large context, RAG, and selective
memory. It saves reproducible Week 6 answer tables in `results/`, including
retrieved event IDs, similarity scores, retrieval coverage, and selective-memory
answers.

For a network-free pipeline check, replace `--engine codex` with
`--engine oracle`. Oracle mode tests file generation and scoring only; it is
not an AI benchmark result.

## Method

TF-IDF is implemented with the Python standard library. Each event is treated
as one document. Retrieval uses cosine similarity and returns five events per
question. Selective memory is generated from the Day 30 state plus linked
historical events, marking facts `Use` or `Ignore`. All three approaches receive
the same questions, model, and keyword-based answer rubric.

The automated rubric labels each answer as Correct, Incomplete, or Incorrect
and identifies common errors such as outdated information, wrong ownership,
missed blockers, and missed requirement changes. The labels are transparent
heuristics, so the saved answers should also be reviewed before reporting the
experiment.

## Observed result

The original Week 4–5 run answered 15/15 questions correctly for both
conditions. The latest timed Week 6 replay scored 23/30 (76.7%) for large
context, 21/30 (70.0%) for RAG, and 25/30 (83.3%) for selective memory under
the transparent keyword rubric. RAG included at least one current supporting
event for 28/30 questions and the full supporting set for 23/30. Selective
memory used 19.0% fewer estimated input tokens than RAG, but the one timed
replay was slower end-to-end (217.326 seconds versus 108.809 seconds). These
are dataset-specific, stochastic results and require manual review.

## Outputs

- `results/week4_large_context_results.csv`
- `results/week5_rag_results.csv`
- `results/comparison.csv`
- `results/summary.md`
- `results/week4_raw.json` and `results/week5_raw.json`
- `results/week6_large_context_results.csv`
- `results/week6_rag_results.csv`
- `results/week6_selective_memory_results.csv`
- `results/week6_comparison.csv` and `results/week6_summary.md`
- `results/week6_efficiency.md`
- `results/week6_large_raw.json`, `results/week6_rag_raw.json`, and `results/week6_selective_raw.json`

## Student explanation

ShieldPath Learning Lab is a fictional privacy-first learning platform whose
30-day history includes task reassignments, resolved and active blockers,
deadline changes, revised requirements, completed work, canceled features, and
replaced technical decisions. The dataset is useful for testing AI memory
because outdated and irrelevant facts remain in the history beside the newer
facts that supersede them. A large-context model can see every update but may
be distracted by conflicts, while a retrieval system reduces context but may
miss the event needed to answer correctly. Comparing both approaches shows
whether more project information improves accuracy or creates confusion.

[Complete the 5-Minute Feedback Form](https://tinyurl.com/5minstudentfeedbackform)

## License

MIT
