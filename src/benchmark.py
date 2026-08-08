#!/usr/bin/env python3
"""Run the large-context, TF-IDF RAG, and selective-memory benchmarks."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SCHEMA = ROOT / "schemas" / "answers.schema.json"
MEMORY_OUTPUT = DATA / "selective_memory.csv"
MEMORY_FIELDS = [
    "Memory Item", "Category", "Current Status", "Original Information",
    "Updated Information", "Use or Ignore", "Supporting Event IDs", "Notes",
]
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "current",
    "currently", "day", "did", "do", "does", "end", "for", "from", "has",
    "have", "in", "is", "it", "of", "on", "or", "project", "still", "the",
    "to", "was", "what", "which", "who", "with",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def event_text(event: dict[str, str]) -> str:
    fields = (
        "Event ID", "Day", "Date", "Update Type", "Task", "Owner", "Status",
        "Blocker", "Requirement Change", "Memory Action", "Validity",
        "Replaces Event", "Note",
    )
    return " | ".join(f"{field}: {event[field]}" for field in fields if event[field])


def memory_event_text(event: dict[str, str]) -> str:
    fields = ("Event ID", "Owner", "Status", "Blocker", "Requirement Change", "Note")
    return "; ".join(f"{field}: {event[field]}" for field in fields if event[field])


def build_selective_memory(
    events: list[dict[str, str]], current_state: list[dict[str, str]]
) -> list[dict[str, str]]:
    events_by_task: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for event in events:
        events_by_task[event["Task"]].append(event)

    rows = []
    ignored_categories = {"Canceled task", "Removed feature", "Replaced technical decision"}
    for state in current_state:
        history = events_by_task[state["Item"]]
        original = memory_event_text(history[0]) if history else ""
        updated = "; ".join(
            f"{label}: {state[field]}"
            for label, field in (
                ("Owner", "Current Owner"),
                ("Status", "Current Status"),
                ("Requirement", "Current Requirement"),
            )
            if state[field]
        )
        use_or_ignore = "Ignore" if state["Category"] in ignored_categories else "Use"
        notes = state["Active Blocker"] or (
            "Historical or canceled information; do not use as current state."
            if use_or_ignore == "Ignore" else ""
        )
        rows.append({
            "Memory Item": state["Item"],
            "Category": state["Category"],
            "Current Status": state["Current Status"],
            "Original Information": original,
            "Updated Information": updated,
            "Use or Ignore": use_or_ignore,
            "Supporting Event IDs": "; ".join(event["Event ID"] for event in history),
            "Notes": notes,
        })

    for event in events:
        if event["Validity"] == "Current":
            continue
        if event["Validity"] not in {"Outdated", "Irrelevant", "Canceled"}:
            continue
        category = "Outdated fact" if event["Validity"] == "Outdated" else "Canceled or irrelevant fact"
        rows.append({
            "Memory Item": event["Task"],
            "Category": category,
            "Current Status": event["Status"],
            "Original Information": memory_event_text(event),
            "Updated Information": "Do not use as current state.",
            "Use or Ignore": "Ignore",
            "Supporting Event IDs": event["Event ID"],
            "Notes": "Historical event marked outdated, canceled, or irrelevant.",
        })
    return rows


def tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS
    ]


def retrieve(question: str, events: list[dict[str, str]], top_k: int) -> list[tuple[float, dict[str, str]]]:
    documents = [tokens(event_text(event)) for event in events]
    query = tokens(question)
    document_frequency = Counter(
        token for document in documents for token in set(document)
    )
    count = len(documents)

    def vector(words: list[str]) -> dict[str, float]:
        frequency = Counter(words)
        return {
            word: value * (math.log((1 + count) / (1 + document_frequency[word])) + 1)
            for word, value in frequency.items()
        }

    query_vector = vector(query)
    query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
    scored = []
    for event, document in zip(events, documents):
        document_vector = vector(document)
        document_norm = math.sqrt(sum(value * value for value in document_vector.values()))
        dot = sum(value * document_vector.get(word, 0) for word, value in query_vector.items())
        score = dot / (query_norm * document_norm) if query_norm and document_norm else 0
        scored.append((score, event))
    return sorted(
        scored,
        key=lambda item: (item[0], int(item[1]["Event ID"][1:])),
        reverse=True,
    )[:top_k]


def prompt_header() -> str:
    return """You are evaluating memory over a fictional 30-day software project.
Answer only from the supplied project updates. Treat each question as asking
about the end of Day 30 unless it explicitly says otherwise. Later replacement
events override earlier facts. For current-state questions, use Current facts
and ignore Outdated or Irrelevant facts. Be concise. Do not use tools, external
sources, or unstated assumptions. Return one answer for every question ID."""


def large_context_prompt(events: list[dict[str, str]], questions: list[dict[str, str]]) -> str:
    updates = "\n".join(event_text(event) for event in events)
    asks = "\n".join(f"{row['Question ID']}: {row['Question']}" for row in questions)
    return f"{prompt_header()}\n\nPROJECT UPDATES:\n{updates}\n\nQUESTIONS:\n{asks}"


def rag_prompt(
    questions: list[dict[str, str]],
    retrieved: dict[str, list[tuple[float, dict[str, str]]]],
) -> str:
    sections = []
    for row in questions:
        question_id = row["Question ID"]
        context = "\n".join(event_text(event) for _, event in retrieved[question_id])
        sections.append(f"{question_id}: {row['Question']}\nRETRIEVED UPDATES:\n{context}")
    return f"{prompt_header()}\n\n" + "\n\n".join(sections)


def selective_memory_prompt(
    questions: list[dict[str, str]], memory: list[dict[str, str]]
) -> str:
    facts = "\n".join(
        " | ".join(f"{field}: {row[field]}" for field in MEMORY_FIELDS if row[field])
        for row in memory
    )
    asks = "\n".join(f"{row['Question ID']}: {row['Question']}" for row in questions)
    instructions = (
        "Use only memory rows marked Use for current answers. Rows marked Ignore "
        "are historical context and must not be treated as current facts. Use the "
        "updated information and source event IDs when a row contains both old "
        "and new information."
    )
    return f"{prompt_header()}\n{instructions}\n\nSELECTIVE MEMORY:\n{facts}\n\nQUESTIONS:\n{asks}"


def run_codex(prompt: str, raw_name: str) -> dict[str, str]:
    RESULTS.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output:
        output_path = Path(output.name)
    command = [
        "codex", "exec", "--ephemeral", "--sandbox", "read-only",
        "--skip-git-repo-check", "--output-schema", str(SCHEMA),
        "--output-last-message", str(output_path), "-",
    ]
    completed = subprocess.run(
        command, input=prompt, text=True, capture_output=True, cwd=ROOT
    )
    try:
        raw = output_path.read_text(encoding="utf-8")
    finally:
        output_path.unlink(missing_ok=True)
    (RESULTS / raw_name).write_text(raw + "\n", encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"codex exec failed: {completed.stderr.strip()}")
    payload = json.loads(raw)
    return {item["question_id"]: item["answer"] for item in payload["answers"]}


def classify(question: dict[str, str], answer: str) -> tuple[str, str]:
    normalized = answer.lower()
    outdated = [
        term.strip().lower()
        for group in question["Outdated Keywords"].split(";")
        for term in group.split("|")
        if term.strip()
    ]
    if any(term in normalized for term in outdated):
        error = {
            "Current owner": "Wrong task owner",
            "Current requirement": "Missed requirement change",
            "Active blocker": "Missed blocker",
            "Contradiction resolution": "Outdated information error",
            "Deadline update": "Outdated information error",
            "Outdated information": "Outdated information error",
        }.get(question["Category"], "Outdated information error")
        return "Incorrect", error

    groups = [
        [choice.strip().lower() for choice in group.split("|")]
        for group in question["Required Keywords"].split(";")
    ]
    matched = [any(choice in normalized for choice in group) for group in groups]
    if all(matched):
        return "Correct", "Correct"
    return ("Incomplete", "Incomplete answer") if any(matched) else ("Incorrect", "Incorrect")


def require_answer_ids(
    questions: list[dict[str, str]], answers: dict[str, str]
) -> None:
    expected = {row["Question ID"] for row in questions}
    actual = set(answers)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual))
        extra = ", ".join(sorted(actual - expected))
        details = "; ".join(part for part in (f"missing: {missing}" if missing else "", f"extra: {extra}" if extra else "") if part)
        raise RuntimeError(f"answer IDs do not match questions ({details})")


def result_rows(
    questions: list[dict[str, str]],
    answers: dict[str, str],
    contexts: dict[str, list[tuple[float, dict[str, str]]]] | None = None,
    condition: str = "large",
) -> list[dict[str, str]]:
    rows = []
    for question in questions:
        question_id = question["Question ID"]
        answer = answers.get(question_id, "")
        status, error = classify(question, answer)
        row = {
            "Question ID": question_id,
            "Question": question["Question"],
            "Correct Answer": question["Correct Answer"],
        }
        if contexts is not None:
            supporting_ids = re.findall(r"E\d{3}", question["Supporting Current Event"])
            retrieved_ids = {event["Event ID"] for _, event in contexts[question_id]}
            row["Retrieved Updates"] = "\n".join(
                f"{event['Event ID']} ({score:.3f}): {event_text(event)}"
                for score, event in contexts[question_id]
            )
            row["RAG Answer"] = answer
            row["Supporting Current Event IDs"] = "; ".join(supporting_ids)
            matched_supporting = retrieved_ids.intersection(supporting_ids)
            row["Supporting Event Retrieved"] = "Yes" if matched_supporting else "No"
            row["Supporting Event Coverage"] = (
                "All" if len(matched_supporting) == len(set(supporting_ids))
                else "Partial" if matched_supporting else "None"
            )
            row["RAG Answer Correct"] = "Yes" if status == "Correct" else "No"
        elif condition == "selective":
            row["Selective-Memory Answer"] = answer
            row["Selective-Memory Answer Correct"] = "Yes" if status == "Correct" else "No"
        else:
            row["AI Answer"] = answer
        row["Correct/Incorrect"] = status
        row["Error Type"] = error
        row["Notes"] = (
            "Matched the answer key."
            if status == "Correct"
            else f"Automated keyword rubric flagged: {error}."
        )
        rows.append(row)
    return rows


def write_summary(
    large_rows: list[dict[str, str]],
    rag_rows: list[dict[str, str]],
    selective_rows: list[dict[str, str]],
) -> None:
    def counts(rows: list[dict[str, str]]) -> Counter:
        return Counter(row["Correct/Incorrect"] for row in rows)

    large, rag = counts(large_rows), counts(rag_rows)
    comparison = []
    for large_row, rag_row, selective_row in zip(large_rows, rag_rows, selective_rows):
        large_status = large_row["Correct/Incorrect"]
        rag_status = rag_row["Correct/Incorrect"]
        rank = {"Incorrect": 0, "Incomplete": 1, "Correct": 2}
        statuses = {
            "Large context": large_status,
            "RAG": rag_status,
            "Selective memory": selective_row["Correct/Incorrect"],
        }
        best = max(rank[status] for status in statuses.values())
        winners = [name for name, status in statuses.items() if rank[status] == best]
        winner = winners[0] if len(winners) == 1 else "Tie"
        comparison.append({
            "Question ID": large_row["Question ID"],
            "Question": large_row["Question"],
            "Large Context Status": large_status,
            "Large Context Error Type": large_row["Error Type"],
            "RAG Status": rag_status,
            "RAG Error Type": rag_row["Error Type"],
            "Supporting Event Retrieved": rag_row["Supporting Event Retrieved"],
            "Supporting Event Coverage": rag_row["Supporting Event Coverage"],
            "RAG Answer Correct": rag_row["RAG Answer Correct"],
            "Selective Memory Status": selective_row["Correct/Incorrect"],
            "Selective Memory Error Type": selective_row["Error Type"],
            "Winner": winner,
            "Notes": "All conditions used the same questions and answer rubric.",
        })
    write_csv(RESULTS / "week6_comparison.csv", comparison, list(comparison[0]))
    total = len(large_rows)
    summary = f"""# RecallBench Results

The large-context baseline answered {large['Correct']}/{total} questions
correctly. The TF-IDF RAG baseline answered {rag['Correct']}/{total} correctly
with the top five retrieved updates per question. Selective memory answered
{counts(selective_rows)['Correct']}/{total} correctly from the generated memory
table.

The top-five retrieval contained at least one supporting event for {sum(row['Supporting Event Retrieved'] == 'Yes' for row in rag_rows)}/{total} questions and the full supporting event set for {sum(row['Supporting Event Coverage'] == 'All' for row in rag_rows)}/{total}. RAG answer correctness is scored separately from retrieval coverage.

| Approach | Correct | Incomplete | Incorrect | Accuracy |
|---|---:|---:|---:|---:|
| Large context | {large['Correct']} | {large['Incomplete']} | {large['Incorrect']} | {large['Correct'] / total:.1%} |
| TF-IDF RAG | {rag['Correct']} | {rag['Incomplete']} | {rag['Incorrect']} | {rag['Correct'] / total:.1%} |
| Selective memory | {counts(selective_rows)['Correct']} | {counts(selective_rows)['Incomplete']} | {counts(selective_rows)['Incorrect']} | {counts(selective_rows)['Correct'] / total:.1%} |

The comparison tests whether smaller retrieved contexts reduce conflict or
instead omit the newer event needed to replace an older fact. Automated labels
use a transparent keyword rubric and should be reviewed alongside the saved
answers before drawing conclusions.

The publication-facing Week 7 manual audit of this replay is recorded in
`results/week7_final_scoring.csv` and summarized in `results/week7_summary.md`.
It preserves these automated labels while adjudicating every non-Correct row.
"""
    (RESULTS / "week6_summary.md").write_text(summary, encoding="utf-8")


def validate() -> None:
    events = read_csv(DATA / "project_updates.csv")
    questions = read_csv(DATA / "evaluation_questions.csv")
    current_state = read_csv(DATA / "day30_current_state.csv")
    assert len(events) == 90, f"expected 90 events, found {len(events)}"
    assert [event["Event ID"] for event in events] == [
        f"E{number:03d}" for number in range(1, 91)
    ]
    assert len(questions) == 30, f"expected 30 questions, found {len(questions)}"
    assert len({row["Question ID"] for row in questions}) == len(questions)
    event_ids = {event["Event ID"] for event in events}
    for row in questions:
        assert row["Required Keywords"], f"{row['Question ID']} has no rubric"
        for field in ("Supporting Current Event", "Conflicting Old Event"):
            for event_id in re.findall(r"E\d{3}", row[field]):
                assert event_id in event_ids, event_id
    assert sum(event["Update Type"] == "Deadline Change" for event in events) >= 4
    assert any(event["Update Type"] == "Feature Revival" for event in events)
    assert any(event["Task"] == "Browser smoke test fixtures" for event in events)
    memory = build_selective_memory(events, current_state)
    assert memory and all(set(MEMORY_FIELDS) == set(row) for row in memory)
    sample = retrieve("Who owns browser smoke tests?", events, 5)
    assert len(sample) == 5 and sample[0][0] > 0
    print("Validated 90 events, 30 questions, memory rows, event references, and TF-IDF retrieval.")


def run(mode: str, engine: str, top_k: int) -> None:
    events = read_csv(DATA / "project_updates.csv")
    questions = read_csv(DATA / "evaluation_questions.csv")
    current_state = read_csv(DATA / "day30_current_state.csv")
    contexts = {
        row["Question ID"]: retrieve(row["Question"], events, top_k)
        for row in questions
    }
    large_rows = rag_rows = selective_rows = None
    if mode in {"large", "all"}:
        answers = (
            {row["Question ID"]: row["Correct Answer"] for row in questions}
            if engine == "oracle"
            else run_codex(large_context_prompt(events, questions), "week6_large_raw.json")
        )
        require_answer_ids(questions, answers)
        large_rows = result_rows(questions, answers, condition="large")
        write_csv(
            RESULTS / "week6_large_context_results.csv",
            large_rows,
            ["Question ID", "Question", "Correct Answer", "AI Answer",
             "Correct/Incorrect", "Error Type", "Notes"],
        )
    if mode in {"rag", "all"}:
        answers = (
            {row["Question ID"]: row["Correct Answer"] for row in questions}
            if engine == "oracle"
            else run_codex(rag_prompt(questions, contexts), "week6_rag_raw.json")
        )
        require_answer_ids(questions, answers)
        rag_rows = result_rows(questions, answers, contexts, condition="rag")
        write_csv(
            RESULTS / "week6_rag_results.csv",
            rag_rows,
            ["Question ID", "Question", "Correct Answer", "Retrieved Updates",
             "RAG Answer", "Supporting Current Event IDs", "Supporting Event Retrieved",
             "Supporting Event Coverage", "RAG Answer Correct", "Correct/Incorrect",
             "Error Type", "Notes"],
        )
    if mode in {"selective", "all"}:
        memory = build_selective_memory(events, current_state)
        write_csv(MEMORY_OUTPUT, memory, MEMORY_FIELDS)
        answers = (
            {row["Question ID"]: row["Correct Answer"] for row in questions}
            if engine == "oracle"
            else run_codex(selective_memory_prompt(questions, memory), "week6_selective_raw.json")
        )
        require_answer_ids(questions, answers)
        selective_rows = result_rows(questions, answers, condition="selective")
        write_csv(
            RESULTS / "week6_selective_memory_results.csv",
            selective_rows,
            ["Question ID", "Question", "Correct Answer", "Selective-Memory Answer",
             "Selective-Memory Answer Correct", "Correct/Incorrect", "Error Type", "Notes"],
        )
    if large_rows is not None and rag_rows is not None and selective_rows is not None:
        write_summary(large_rows, rag_rows, selective_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--mode", choices=("large", "rag", "selective", "all"), default="all")
    run_parser.add_argument("--engine", choices=("codex", "oracle"), default="codex")
    run_parser.add_argument("--top-k", type=int, choices=range(3, 6), default=5)
    args = parser.parse_args()
    if args.command == "validate":
        validate()
    else:
        run(args.mode, args.engine, args.top_k)


if __name__ == "__main__":
    main()
