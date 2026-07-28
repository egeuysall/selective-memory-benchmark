# Selective Memory in AI Agents

This repository contains the Week 4 and Week 5 experiments for **Selective
Memory in AI Agents: A Benchmark for Long-Term Project Support**. It compares:

1. a large-context baseline that receives all 86 project updates; and
2. a simple RAG baseline that receives the five highest-scoring TF-IDF updates
   for each question.

The benchmark uses 15 questions about current owners, completed and delayed
tasks, blockers, changed requirements, canceled work, and conflicts between old
and new facts. The fictional ShieldPath Learning Lab timeline was inspired by
activity from a real student software project and transformed into a fictional
benchmark.

## Data

- [Public Week 3 Google Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vShzbDGNay0SFVU8jsFeOO9Xr_NNcNiKUxvRHrRnYnJBZkybYBQs2o0X3mJe8akU0riTyxe6lF2_Exh/pubhtml)
- `data/project_updates.csv`: the 86-event, 30-day timeline
- `data/day30_current_state.csv`: the final selective-memory state
- `data/evaluation_questions.csv`: 15 questions and answer rubric

No private project data, credentials, or contact details are included.

## Run locally

Requirements: Python 3.11 or newer and an authenticated
[Codex CLI](https://developers.openai.com/codex/cli).

```bash
python3 src/benchmark.py validate
python3 -m unittest discover -s tests -v
python3 src/benchmark.py run --mode all --engine codex --top-k 5
```

The final command makes two model calls: one for all large-context questions
and one for all RAG questions. It saves reproducible answer tables in
`results/`, including the retrieved event IDs and similarity scores.

For a network-free pipeline check, replace `--engine codex` with
`--engine oracle`. Oracle mode tests file generation and scoring only; it is
not an AI benchmark result.

## Method

TF-IDF is implemented with the Python standard library. Each event is treated
as one document. Retrieval uses cosine similarity and returns five events per
question. Both approaches receive the same instructions, questions, model, and
keyword-based answer rubric. This holds the answering method constant while
changing how much project history is supplied.

The automated rubric labels each answer as Correct, Incomplete, or Incorrect
and identifies common errors such as outdated information, wrong ownership,
missed blockers, and missed requirement changes. The labels are transparent
heuristics, so the saved answers should also be reviewed before reporting the
experiment.

## Observed result

In the recorded run, both approaches answered 15 of 15 questions correctly.
The top-five TF-IDF context was sufficient for every question, so reducing the
context did not improve or reduce accuracy in this first test. The retrieved
rows and raw model answers remain saved for manual review and later comparison
with a selective-memory approach.

## Outputs

- `results/week4_large_context_results.csv`
- `results/week5_rag_results.csv`
- `results/comparison.csv`
- `results/summary.md`
- `results/week4_raw.json` and `results/week5_raw.json`

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
