#!/usr/bin/env python3
"""Create the Week 7 audited scoring table from the saved Week 6 replay."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"

CONDITIONS = {
    "Large context": ("week6_large_context_results.csv", "AI Answer"),
    "Traditional TF-IDF RAG": ("week6_rag_results.csv", "RAG Answer"),
    "Selective memory": ("week6_selective_memory_results.csv", "Selective-Memory Answer"),
}

# These are the only rows that the keyword rubric did not label Correct. The
# audit preserves the raw labels and records every human override explicitly.
DECISIONS = {
    ("Large context", "Q16"): (
        "Incorrect",
        "Multi-owner history",
        "The answer contradicts the event history by saying no task changed owner more than once.",
    ),
    ("Large context", "Q17"): (
        "Partially correct",
        "Missed blocker transition",
        "It gives a real resolved-paths to keyboard-only transition, but substitutes that chain for the benchmark's browser-dependency transition.",
    ),
    ("Large context", "Q21"): (
        "Correct",
        "Keyword-rubric false negative",
        "It names the Live Help offline fallback. The removed-from-MVP and future-backlog relation is already stated in the question and the answer makes no contrary claim.",
    ),
    ("Large context", "Q25"): (
        "Partially correct",
        "Canceled/obsolete scope",
        "It names two canceled features, omits the guided paths desktop mockup, and adds an unlisted experimental recovery branch.",
    ),
    ("Large context", "Q27"): (
        "Correct",
        "Keyword-rubric false negative",
        "The question asks which older deadline is wrong; July 13, 2026 is the complete answer.",
    ),
    ("Large context", "Q28"): (
        "Correct",
        "Keyword-rubric false negative",
        "The answer semantically covers Aryan's ownership, the mobile-first paths, and preserved course links.",
    ),
    ("Large context", "Q30"): (
        "Correct",
        "Keyword-rubric false negative",
        "It states incomplete keyboard-only coverage, the July 17 MVP target, and the July 19 bounded cleanup target.",
    ),
    ("Traditional TF-IDF RAG", "Q12"): (
        "Partially correct",
        "Missed QA rule detail",
        "It correctly describes changed-file checks and the allowlist, but omits the rule to ignore HTML comments.",
    ),
    ("Traditional TF-IDF RAG", "Q14"): (
        "Correct",
        "Keyword-rubric false negative",
        "It correctly says root deployment routing was fixed and covered by smoke tests.",
    ),
    ("Traditional TF-IDF RAG", "Q16"): (
        "Incorrect",
        "Multi-owner history",
        "It names an MVP owner sequence instead of the two tasks with repeated owner changes.",
    ),
    ("Traditional TF-IDF RAG", "Q17"): (
        "Partially correct",
        "Missed blocker transition",
        "It identifies the later keyboard-only blocker but substitutes the legacy-path blocker for the requested browser-dependency transition.",
    ),
    ("Traditional TF-IDF RAG", "Q21"): (
        "Correct",
        "Keyword-rubric false negative",
        "It identifies the Live Help fallback and its future-backlog status; the additional revival detail does not contradict the answer.",
    ),
    ("Traditional TF-IDF RAG", "Q24"): (
        "Partially correct",
        "Missed recovery requirement detail",
        "It rejects silent restore and mentions recovery controls, but omits the visible recovered state, confirmed discard, and challenge-scoped storage details.",
    ),
    ("Traditional TF-IDF RAG", "Q25"): (
        "Partially correct",
        "Canceled/obsolete scope",
        "It names two canceled features, omits standalone terminal demo mode, and adds the experimental recovery branch.",
    ),
    ("Traditional TF-IDF RAG", "Q28"): (
        "Correct",
        "Keyword-rubric false negative",
        "It semantically covers Aryan's ownership, manual navigation, and preserved course links.",
    ),
    ("Traditional TF-IDF RAG", "Q29"): (
        "Partially correct",
        "Irrelevant-information overinclusion",
        "It includes the two keyed temporary items, but adds unrelated canceled or fixture information and is not precise about the requested pair.",
    ),
    ("Selective memory", "Q17"): (
        "Correct",
        "Keyword-rubric false negative",
        "The hyphenated wording still states the browser-installation resolution followed by incomplete keyboard-only coverage.",
    ),
    ("Selective memory", "Q21"): (
        "Correct",
        "Keyword-rubric false negative",
        "It identifies the Live Help fallback and future-backlog disposition; its expanded description is consistent with the source event.",
    ),
    ("Selective memory", "Q23"): (
        "Incorrect",
        "Event provenance",
        "The question asks for E081 and E086, but the answer cites E084, E085, E089, and E090 instead.",
    ),
    ("Selective memory", "Q24"): (
        "Correct",
        "Keyword-rubric false negative",
        "It includes visible recovery, confirmed discard, challenge-scoped storage, and the old silent-only fact to ignore.",
    ),
    ("Selective memory", "Q30"): (
        "Correct",
        "Keyword-rubric false negative",
        "It states the incomplete keyboard-only coverage and both current delayed targets; the resolved-blocker wording is not an outdated deadline claim.",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    questions = {row["Question ID"]: row for row in read_csv(DATA / "evaluation_questions.csv")}
    results = {
        name: {row["Question ID"]: row for row in read_csv(RESULTS / filename)}
        for name, (filename, _) in CONDITIONS.items()
    }
    question_ids = list(questions)
    final_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []

    for approach, (_, answer_field) in CONDITIONS.items():
        for question_id in question_ids:
            question = questions[question_id]
            result = results[approach][question_id]
            automated = result["Correct/Incorrect"]
            decision = DECISIONS.get((approach, question_id))
            if automated == "Correct":
                label, error_type, reason = "Correct", "None", "Automated label was Correct; no override was needed."
                review_status = "Automated-correct row"
                signoff = "Not required for initial audit"
            else:
                if decision is None:
                    raise AssertionError(f"Missing audit decision for {approach} {question_id}")
                label, error_type, reason = decision
                review_status = "Adjudicated from saved answer"
                signoff = "Pending independent human confirmation"

            final_rows.append({
                "Question ID": question_id,
                "Approach": approach,
                "Question": question["Question"],
                "Answer": result[answer_field],
                "Expected Answer": question["Correct Answer"],
                "Automated Label": automated,
                "Manual Label": label,
                "Published Correct": "Yes" if label == "Correct" else "No",
                "Manual Error Type": error_type,
                "Supporting Event IDs": question["Supporting Current Event"],
                "Conflicting Event IDs": question["Conflicting Old Event"],
                "Review Status": review_status,
                "Review Reason": reason,
                "Independent Sign-off": signoff,
            })
            if automated != "Correct":
                review_rows.append({
                    "Question ID": question_id,
                    "Approach": approach,
                    "Automated Label": automated,
                    "Manual Label": label,
                    "Manual Error Type": error_type,
                    "Answer": result[answer_field],
                    "Expected Answer": question["Correct Answer"],
                    "Supporting Event IDs": question["Supporting Current Event"],
                    "Conflicting Event IDs": question["Conflicting Old Event"],
                    "Review Reason": reason,
                    "Review Status": review_status,
                    "Independent Sign-off": signoff,
                })

    final_fields = list(final_rows[0])
    review_fields = list(review_rows[0])
    write_csv(RESULTS / "week7_final_scoring.csv", final_rows)
    write_csv(RESULTS / "week7_manual_review.csv", review_rows)

    by_approach = {
        approach: [row for row in final_rows if row["Approach"] == approach]
        for approach in CONDITIONS
    }
    ranks = {"Incorrect": 0, "Partially correct": 1, "Correct": 2}
    selective_wins = []
    for question_id in question_ids:
        labels = {
            approach: next(row["Manual Label"] for row in rows if row["Question ID"] == question_id)
            for approach, rows in by_approach.items()
        }
        best = max(ranks[label] for label in labels.values())
        winners = [approach for approach, label in labels.items() if ranks[label] == best]
        if winners == ["Selective memory"]:
            selective_wins.append(question_id)

    def count(approach: str, field: str, value: str) -> int:
        return sum(row[field] == value for row in by_approach[approach])

    summary_lines = [
        "# Week 7 Scoring and Analysis",
        "",
        "This is the publication-facing score for the saved Week 6 live replay.",
        "The original automated keyword labels remain in the Week 6 CSVs; this",
        "audited table records the manual adjudication of every non-Correct row.",
        "The headline score counts only `Correct` as correct and does not combine",
        "accuracy, token cost, or time into a subjective composite.",
        "",
        "## Final audited result",
        "",
        "| Approach | Correct | Partially correct | Incorrect | Accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for approach in CONDITIONS:
        correct = count(approach, "Manual Label", "Correct")
        partial = count(approach, "Manual Label", "Partially correct")
        incorrect = count(approach, "Manual Label", "Incorrect")
        summary_lines.append(f"| {approach} | {correct} | {partial} | {incorrect} | {correct / len(question_ids):.1%} |")
    summary_lines += [
        "",
        "The reconciled final manuscript numbers are therefore **large context",
        "27/30 (90.0%)**, **traditional TF-IDF RAG 24/30 (80.0%)**, and",
        "**selective memory 29/30 (96.7%)**. The older 24/22/26 replay is",
        "historical only; the automated labels for the current replay are retained",
        "as 23/21/25 for auditability.",
        "",
        "## Automated versus audited labels",
        "",
        "| Approach | Automated correct | Audited correct | Rows promoted after review |",
        "|---|---:|---:|---:|",
    ]
    for approach in CONDITIONS:
        auto = count(approach, "Automated Label", "Correct")
        audited = count(approach, "Manual Label", "Correct")
        summary_lines.append(f"| {approach} | {auto}/30 | {audited}/30 | {audited - auto} |")
    summary_lines += [
        "",
        "Promotions are wording-level false negatives or semantically complete",
        "answers identified during the manual audit; they are not hidden changes",
        "to the saved model answers.",
        "",
        "## Where selective memory helped",
        "",
        "Selective memory was the only approach with the highest audited label on:",
        "",
    ]
    summary_lines += [f"- `{question_id}`" for question_id in selective_wins]
    summary_lines += [
        "",
        "These are the examples to inspect in the Results and Discussion sections.",
        "",
        "## Selective-memory failure",
        "",
        "| Question | Audited label | Cause |",
        "|---|---|---|",
    ]
    for row in by_approach["Selective memory"]:
        if row["Manual Label"] != "Correct":
            summary_lines.append(f"| `{row['Question ID']}` | {row['Manual Label']} | {row['Manual Error Type']}: {row['Review Reason']} |")
    summary_lines += [
        "",
        "The selective-memory miss is an event-provenance error: the answer",
        "described nearby keyboard-coverage changes but did not cite the two",
        "events requested by the question (E081 and E086).",
        "",
        "## Audited error categories",
        "",
        "| Error category | Large context | Traditional TF-IDF RAG | Selective memory |",
        "|---|---:|---:|---:|",
    ]
    categories = sorted({
        row["Manual Error Type"]
        for row in final_rows
        if row["Manual Label"] != "Correct"
    })
    for category in categories:
        summary_lines.append("| " + category + " | " + " | ".join(
            str(sum(row["Manual Error Type"] == category and row["Manual Label"] != "Correct" for row in by_approach[approach]))
            for approach in CONDITIONS
        ) + " |")
    summary_lines += [
        "",
        "## RAG retrieval coverage",
        "",
        "The top-five RAG context retrieved at least one supporting current event",
        "for 28/30 questions, all supporting events for 23/30, a partial set for",
        "5/30, and none for 2/30. Retrieval coverage and answer correctness remain",
        "separate measures.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 src/week7_audit.py",
        "python3 visual_benchmark/build_report.py --check",
        "```",
        "",
        "The visual benchmark is [the Vercel-style SVG](../visual_benchmark/benchmark.svg).",
        "Its price comparison is an estimated token-cost proxy because the Codex",
        "replay did not expose billable USD or a model price schedule.",
        "",
        "Independent human sign-off is still required before manuscript submission",
        "because this audit is a single reviewer pass over one stochastic replay.",
        "",
    ]
    (RESULTS / "week7_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print("Wrote week7_final_scoring.csv, week7_manual_review.csv, and week7_summary.md")
    print("Selective-only audited wins:", ", ".join(selective_wins))


if __name__ == "__main__":
    main()
