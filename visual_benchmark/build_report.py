#!/usr/bin/env python3
"""Build the dependency-free, Vercel-style benchmark report."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import benchmark  # noqa: E402

METHODS = [
    ("Large context", "large"),
    ("Traditional TF-IDF RAG", "rag"),
    ("Selective memory", "selective"),
]

# These are the wall times recorded in results/week6_efficiency.md and the
# timed large-context replay. They are one observed replay, not a latency SLA.
WALL_SECONDS = {
    "Large context": 150.057,
    "Traditional TF-IDF RAG": 108.809,
    "Selective memory": 217.326,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def ceil_tokens(characters: int) -> int:
    return math.ceil(characters / 4)


def count(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(row[field] == value for row in rows)


def build_snapshot() -> dict:
    final_rows = read_csv(RESULTS / "week7_final_scoring.csv")
    final = defaultdict(list)
    for row in final_rows:
        final[row["Approach"]].append(row)

    events = benchmark.read_csv(benchmark.DATA / "project_updates.csv")
    questions = benchmark.read_csv(benchmark.DATA / "evaluation_questions.csv")
    current_state = benchmark.read_csv(benchmark.DATA / "day30_current_state.csv")
    memory = benchmark.build_selective_memory(events, current_state)
    retrieved = {
        row["Question ID"]: benchmark.retrieve(row["Question"], events, 5)
        for row in questions
    }
    prompts = {
        "Large context": benchmark.large_context_prompt(events, questions),
        "Traditional TF-IDF RAG": benchmark.rag_prompt(questions, retrieved),
        "Selective memory": benchmark.selective_memory_prompt(questions, memory),
    }
    raw_files = {
        "Large context": "week6_large_raw.json",
        "Traditional TF-IDF RAG": "week6_rag_raw.json",
        "Selective memory": "week6_selective_raw.json",
    }

    methods = []
    for approach, key in METHODS:
        rows = final[approach]
        raw = json.loads((RESULTS / raw_files[approach]).read_text(encoding="utf-8"))
        answer_chars = sum(len(answer["answer"]) for answer in raw["answers"])
        prompt_chars = len(prompts[approach])
        auto_correct = count(rows, "Automated Label", "Correct")
        audited_correct = count(rows, "Manual Label", "Correct")
        methods.append({
            "name": approach,
            "key": key,
            "questions": len(rows),
            "automated_correct": auto_correct,
            "automated_accuracy": auto_correct / len(rows),
            "audited_correct": audited_correct,
            "audited_accuracy": audited_correct / len(rows),
            "audited_partial": count(rows, "Manual Label", "Partially correct"),
            "audited_incorrect": count(rows, "Manual Label", "Incorrect"),
            "prompt_chars": prompt_chars,
            "input_token_proxy": ceil_tokens(prompt_chars),
            "answer_chars": answer_chars,
            "output_token_proxy": ceil_tokens(answer_chars),
            "total_token_proxy": ceil_tokens(prompt_chars) + ceil_tokens(answer_chars),
            "wall_seconds": WALL_SECONDS[approach],
            "manual_error_counts": dict(Counter(
                row["Manual Error Type"]
                for row in rows
                if row["Manual Label"] != "Correct"
            )),
        })

    rag_rows = read_csv(RESULTS / "week6_rag_results.csv")
    coverage = Counter(row["Supporting Event Coverage"] for row in rag_rows)
    retrieval_any = sum(row["Supporting Event Retrieved"] == "Yes" for row in rag_rows)

    ranks = {"Incorrect": 0, "Partially correct": 1, "Correct": 2}
    question_matrix = []
    selective_wins = []
    for question in questions:
        qid = question["Question ID"]
        labels = {
            approach: next(row["Manual Label"] for row in final[approach] if row["Question ID"] == qid)
            for approach, _ in METHODS
        }
        best = max(ranks[label] for label in labels.values())
        winners = [approach for approach, label in labels.items() if ranks[label] == best]
        if winners == ["Selective memory"]:
            selective_wins.append(qid)
        question_matrix.append({
            "id": qid,
            "question": question["Question"],
            "labels": labels,
            "winner": winners[0] if len(winners) == 1 else "Tie",
        })

    snapshot = {
        "title": "Selective memory benchmark",
        "run": {
            "date": "2026-08-06",
            "engine": "Codex CLI",
            "top_k": 5,
            "events": len(events),
            "questions": len(questions),
            "timing_note": "One timed replay per condition; wall time is observational.",
            "cost_note": "Estimated token proxy using ceil(characters / 4); billable USD was not exposed.",
        },
        "methods": methods,
        "rag_coverage": {
            "any_supporting_event": retrieval_any,
            "all": coverage["All"],
            "partial": coverage["Partial"],
            "none": coverage["None"],
        },
        "selective_wins": selective_wins,
        "question_matrix": question_matrix,
        "sources": [
            "results/week7_final_scoring.csv",
            "results/week7_summary.md",
            "results/week6_efficiency.md",
            "data/evaluation_questions.csv",
        ],
    }
    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot: dict) -> None:
    assert snapshot["run"]["events"] == 90
    assert snapshot["run"]["questions"] == 30
    assert len(snapshot["methods"]) == 3
    assert all(method["questions"] == 30 for method in snapshot["methods"])
    assert all(0 < method["audited_correct"] < 30 for method in snapshot["methods"])
    assert snapshot["rag_coverage"]["any_supporting_event"] == 28
    assert snapshot["rag_coverage"]["all"] == 23
    assert snapshot["rag_coverage"]["partial"] == 5
    assert snapshot["rag_coverage"]["none"] == 2
    assert snapshot["selective_wins"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def svg_accuracy(methods: list[dict]) -> str:
    width, height = 760, 360
    left, top, bottom, plot_h = 62, 32, 66, 238
    max_value = 100
    group_w = 190
    colors = ("#a1a1aa", "#111111")
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="accuracy-title accuracy-desc">',
           '<title id="accuracy-title">Automated and audited accuracy by approach</title>',
           '<desc id="accuracy-desc">Audited accuracy is higher for every approach because the manual review corrected wording-level keyword false negatives.</desc>']
    for tick in (0, 25, 50, 75, 100):
        y = top + plot_h - plot_h * tick / max_value
        out.append(f'<line class="gridline" x1="{left}" y1="{y:.1f}" x2="{width - 22}" y2="{y:.1f}" />')
        out.append(f'<text class="axis-label" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{tick}%</text>')
    out.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" />')
    out.append(f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{width - 22}" y2="{top + plot_h}" />')
    for index, method in enumerate(methods):
        x = left + 54 + index * group_w
        for offset, (field, color) in enumerate(zip(("automated_accuracy", "audited_accuracy"), colors)):
            value = method[field] * 100
            bar_h = plot_h * value / max_value
            bar_x = x + offset * 39
            bar_y = top + plot_h - bar_h
            out.append(f'<rect x="{bar_x}" y="{bar_y:.1f}" width="30" height="{bar_h:.1f}" fill="{color}" rx="2" />')
            out.append(f'<text class="bar-label" x="{bar_x + 15}" y="{max(top + 14, bar_y - 7):.1f}" text-anchor="middle">{value:.1f}</text>')
        out.append(f'<text class="x-label" x="{x + 34}" y="{top + plot_h + 28}" text-anchor="middle">{esc(method["name"].replace("Traditional TF-IDF ", "TF-IDF "))}</text>')
    out += [
        '<rect x="552" y="12" width="11" height="11" fill="#a1a1aa" rx="2" /><text class="legend" x="570" y="22">Automated</text>',
        '<rect x="647" y="12" width="11" height="11" fill="#111111" rx="2" /><text class="legend" x="665" y="22">Audited</text>',
        '</svg>',
    ]
    return "".join(out)


def svg_outcomes(methods: list[dict]) -> str:
    width, height = 760, 300
    left, top, plot_h = 62, 28, 190
    group_w = 190
    colors = {"audited_correct": "#111111", "audited_partial": "#737373", "audited_incorrect": "#d4d4d8"}
    labels = (("audited_correct", "Correct"), ("audited_partial", "Partially correct"), ("audited_incorrect", "Incorrect"))
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="outcomes-title outcomes-desc">',
           '<title id="outcomes-title">Audited outcome mix</title>',
           '<desc id="outcomes-desc">Each bar totals thirty questions and separates correct, partially correct, and incorrect answers.</desc>']
    for tick in (0, 50, 100):
        y = top + plot_h - plot_h * tick / 100
        out.append(f'<line class="gridline" x1="{left}" y1="{y:.1f}" x2="{width - 22}" y2="{y:.1f}" />')
        out.append(f'<text class="axis-label" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{tick}%</text>')
    out.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" />')
    out.append(f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{width - 22}" y2="{top + plot_h}" />')
    for index, method in enumerate(methods):
        x = left + 75 + index * group_w
        y = top + plot_h
        for field, label in labels:
            value = method[field] / method["questions"] * 100
            h = plot_h * value / 100
            y -= h
            out.append(f'<rect x="{x}" y="{y:.1f}" width="72" height="{h:.1f}" fill="{colors[field]}" />')
            if h > 18:
                text_color = "#ffffff" if field == "audited_correct" else "#111111"
                out.append(f'<text x="{x + 36}" y="{y + h / 2 + 4:.1f}" text-anchor="middle" fill="{text_color}" class="segment-label">{value:.0f}%</text>')
        out.append(f'<text class="x-label" x="{x + 36}" y="{top + plot_h + 28}" text-anchor="middle">{esc(method["name"].replace("Traditional TF-IDF ", "TF-IDF "))}</text>')
    legend_y = height - 20
    x = 182
    for field, label in labels:
        out.append(f'<rect x="{x}" y="{legend_y - 9}" width="11" height="11" fill="{colors[field]}" /><text class="legend" x="{x + 17}" y="{legend_y}">{label}</text>')
        x += 132 if field != "audited_partial" else 153
    out.append('</svg>')
    return "".join(out)


def svg_coverage(coverage: dict) -> str:
    width, height = 760, 300
    left, top, bar_w, bar_h = 110, 34, 560, 42
    total = sum(coverage[key] for key in ("all", "partial", "none"))
    colors = {"all": "#111111", "partial": "#737373", "none": "#d4d4d8"}
    names = {"all": "All supporting events", "partial": "Partial set", "none": "None"}
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="coverage-title coverage-desc">',
           '<title id="coverage-title">RAG supporting-event coverage</title>',
           '<desc id="coverage-desc">The top-five RAG context retrieved at least one supporting event for twenty-eight of thirty questions.</desc>',
           f'<text class="chart-note" x="{left}" y="22">At least one supporting event: {coverage["any_supporting_event"]}/30 ({coverage["any_supporting_event"] / total:.1%})</text>']
    cursor = left
    for key in ("all", "partial", "none"):
        w = bar_w * coverage[key] / total
        out.append(f'<rect x="{cursor:.1f}" y="{top}" width="{w:.1f}" height="{bar_h}" fill="{colors[key]}" />')
        if w > 42:
            color = "#ffffff" if key == "all" else "#111111"
            out.append(f'<text class="segment-label" fill="{color}" x="{cursor + w / 2:.1f}" y="{top + 27}" text-anchor="middle">{coverage[key]}</text>')
        cursor += w
    for index, key in enumerate(("all", "partial", "none")):
        y = top + 88 + index * 42
        out.append(f'<rect x="{left}" y="{y - 10}" width="11" height="11" fill="{colors[key]}" /><text class="legend" x="{left + 18}" y="{y}">{names[key]}</text><text class="legend-value" x="{width - 90}" y="{y}" text-anchor="end">{coverage[key]}/30</text>')
    out.append('</svg>')
    return "".join(out)


def svg_tradeoff(methods: list[dict]) -> str:
    width, height = 760, 360
    left, top, right, bottom = 76, 30, 32, 66
    plot_w, plot_h = width - left - right, height - top - bottom
    max_cost = max(method["total_token_proxy"] for method in methods) * 1.18
    max_time = max(method["wall_seconds"] for method in methods) * 1.18
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="tradeoff-title tradeoff-desc">',
           '<title id="tradeoff-title">Estimated token-cost proxy versus wall time</title>',
           '<desc id="tradeoff-desc">Each point is one benchmark condition. Lower and left means less proxy context and faster observed time; accuracy is labeled on each point.</desc>']
    for tick in (0, 5000, 10000, 15000):
        if tick > max_cost:
            continue
        x = left + plot_w * tick / max_cost
        out.append(f'<line class="gridline" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" /><text class="axis-label" x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle">{tick // 1000}k</text>')
    for tick in (0, 60, 120, 180, 240):
        if tick > max_time:
            continue
        y = top + plot_h - plot_h * tick / max_time
        out.append(f'<line class="gridline" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" /><text class="axis-label" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{tick}s</text>')
    out.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" /><line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" />')
    positions = [(0, -10), (0, 18), (0, -10)]
    for method, (dx, dy) in zip(methods, positions):
        x = left + plot_w * method["total_token_proxy"] / max_cost
        y = top + plot_h - plot_h * method["wall_seconds"] / max_time
        label = method["name"].replace("Traditional TF-IDF ", "TF-IDF ")
        if method["name"] == "Selective memory":
            label = "Selective memory"
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#111111" /><text class="point-label" x="{x + dx + 11:.1f}" y="{y + dy:.1f}">{esc(label)} · {pct(method["audited_accuracy"])}</text>')
    out += [
        f'<text class="axis-title" x="{left + plot_w / 2}" y="{height - 12}" text-anchor="middle">Estimated total token-cost proxy (lower is cheaper)</text>',
        f'<text class="axis-title" transform="translate(16 {top + plot_h / 2}) rotate(-90)" text-anchor="middle">Observed wall time (lower is faster)</text>',
        '</svg>',
    ]
    return "".join(out)


def svg_errors(methods: list[dict]) -> str:
    categories = sorted({category for method in methods for category in method["manual_error_counts"]})
    width, row_h, height = 760, 38, 56 + len(categories) * 38
    left, label_w, plot_w = 245, 0, 430
    max_value = max((method["manual_error_counts"].get(category, 0) for method in methods for category in categories), default=1)
    colors = ("#111111", "#737373", "#d4d4d8")
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="errors-title errors-desc">',
           '<title id="errors-title">Audited error categories</title>',
           '<desc id="errors-desc">Counts of non-correct answers after manual review, grouped by error category.</desc>']
    for index, category in enumerate(categories):
        y = 36 + index * row_h
        out.append(f'<text class="row-label" x="0" y="{y + 4}">{esc(category)}</text>')
        for method_index, method in enumerate(methods):
            value = method["manual_error_counts"].get(category, 0)
            bar_y = y - 15 + method_index * 10
            bar_w = plot_w * value / max_value if max_value else 0
            out.append(f'<rect x="{left}" y="{bar_y}" width="{bar_w:.1f}" height="7" fill="{colors[method_index]}" rx="1" /><text class="tiny-label" x="{left + bar_w + 5:.1f}" y="{bar_y + 7}">{value}</text>')
    out += [
        '<rect x="245" y="14" width="10" height="10" fill="#111111" /><text class="legend" x="261" y="23">Large context</text>',
        '<rect x="354" y="14" width="10" height="10" fill="#737373" /><text class="legend" x="370" y="23">TF-IDF RAG</text>',
        '<rect x="452" y="14" width="10" height="10" fill="#d4d4d8" /><text class="legend" x="468" y="23">Selective memory</text>',
        '</svg>',
    ]
    return "".join(out)


def method_table(methods: list[dict]) -> str:
    rows = []
    for method in methods:
        rows.append(
            f'<tr><th scope="row">{esc(method["name"])}</th>'
            f'<td>{method["audited_correct"]}/30 ({pct(method["audited_accuracy"])})</td>'
            f'<td>{method["automated_correct"]}/30 ({pct(method["automated_accuracy"])})</td>'
            f'<td>{method["total_token_proxy"]:,}</td>'
            f'<td>{method["wall_seconds"]:.3f}s</td></tr>'
        )
    return "".join(rows)


def matrix_table(snapshot: dict) -> str:
    rows = []
    for item in snapshot["question_matrix"]:
        cells = []
        for method, _ in METHODS:
            label = item["labels"][method]
            short = {"Correct": "C", "Partially correct": "P", "Incorrect": "I"}[label]
            cls = {"Correct": "good", "Partially correct": "partial", "Incorrect": "bad"}[label]
            cells.append(f'<td class="status {cls}" title="{esc(label)}">{short}</td>')
        rows.append(f'<tr><th scope="row">{item["id"]}</th><td>{esc(item["question"])}</td>{"".join(cells)}<td>{esc(item["winner"])}</td></tr>')
    return "".join(rows)


def render_report(snapshot: dict) -> str:
    methods = snapshot["methods"]
    coverage = snapshot["rag_coverage"]
    method_rows = method_table(methods)
    matrix_rows = matrix_table(snapshot)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(snapshot["title"])}</title>
<style>
:root {{ color-scheme: light; --ink:#111; --muted:#666; --line:#eaeaea; --soft:#fafafa; --good:#111; --partial:#737373; --bad:#d4d4d8; font-family: Geist, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--ink); background:#fff; font-size:15px; line-height:1.55; }}
a {{ color:inherit; }}
.shell {{ width:min(1200px, calc(100% - 48px)); margin:0 auto; }}
header {{ border-bottom:1px solid var(--line); padding:72px 0 42px; }}
.eyebrow {{ font:12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }}
h1 {{ font-size:clamp(40px, 7vw, 76px); line-height:.98; letter-spacing:-.065em; max-width:850px; margin:18px 0 24px; font-weight:650; }}
h2 {{ font-size:24px; line-height:1.1; letter-spacing:-.03em; margin:0 0 10px; }}
h3 {{ font-size:16px; margin:0 0 8px; }}
p {{ max-width:720px; color:var(--muted); margin:0 0 16px; }}
.lede {{ font-size:18px; max-width:700px; }}
.meta {{ display:flex; flex-wrap:wrap; gap:10px 24px; margin-top:26px; color:var(--muted); font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
main {{ padding:42px 0 80px; }}
.grid {{ display:grid; grid-template-columns:repeat(12, minmax(0,1fr)); gap:18px; }}
.span-12 {{ grid-column:span 12; }} .span-6 {{ grid-column:span 6; }}
.panel {{ border-top:1px solid var(--ink); padding-top:18px; margin-bottom:28px; }}
.panel-note {{ font:12px ui-monospace, SFMono-Regular, Menlo, monospace; color:var(--muted); margin:14px 0 0; }}
.summary {{ border-bottom:1px solid var(--line); padding-bottom:28px; margin-bottom:48px; }}
.summary-grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:1px; background:var(--line); border:1px solid var(--line); margin-top:28px; }}
.summary-item {{ background:#fff; padding:20px; }}
.summary-value {{ display:block; font-size:31px; letter-spacing:-.04em; line-height:1; margin:8px 0; }}
.summary-label {{ color:var(--muted); font:11px ui-monospace, SFMono-Regular, Menlo, monospace; text-transform:uppercase; letter-spacing:.06em; }}
.chart {{ width:100%; overflow-x:auto; margin-top:18px; }}
svg {{ display:block; width:100%; min-width:620px; height:auto; }}
.gridline {{ stroke:#ededed; stroke-width:1; }} .axis {{ stroke:#111; stroke-width:1.2; }}
.axis-label,.legend,.legend-value,.chart-note {{ fill:#666; font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
.x-label,.row-label {{ fill:#111; font:12px Geist, ui-sans-serif, sans-serif; }}
.bar-label,.point-label {{ fill:#111; font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
.axis-title {{ fill:#666; font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }}
.segment-label {{ font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }} .tiny-label {{ fill:#111; font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ border-bottom:1px solid var(--line); padding:12px 10px; text-align:left; vertical-align:top; }}
thead th {{ color:var(--muted); font:11px ui-monospace, SFMono-Regular, Menlo, monospace; text-transform:uppercase; letter-spacing:.05em; }}
tbody th {{ font-weight:500; }}
.status {{ width:54px; text-align:center; font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
.status.good {{ background:#111; color:#fff; }} .status.partial {{ background:#737373; color:#fff; }} .status.bad {{ background:#e4e4e7; color:#111; }}
.matrix-wrap {{ max-height:560px; overflow:auto; border-bottom:1px solid var(--line); }}
.matrix-wrap table {{ min-width:900px; }} .matrix-wrap thead {{ position:sticky; top:0; background:#fff; z-index:1; }}
.callout {{ border-left:3px solid #111; padding:2px 0 2px 16px; margin:18px 0; }}
code {{ font:12px ui-monospace, SFMono-Regular, Menlo, monospace; background:var(--soft); padding:2px 5px; }}
footer {{ border-top:1px solid var(--line); padding:22px 0 50px; color:var(--muted); font-size:13px; }}
@media (max-width:760px) {{ .shell {{ width:min(100% - 28px, 1200px); }} header {{ padding-top:42px; }} .span-6 {{ grid-column:span 12; }} .summary-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:48px; }} }}
</style>
</head>
<body>
<header><div class="shell">
<div class="eyebrow">RecallBench / Week 7 / audited replay</div>
<h1>Accuracy, cost, and time—kept separate.</h1>
<p class="lede">A restrained benchmark view for the same 30 questions across large-context prompting, traditional TF-IDF RAG, and selective memory.</p>
<div class="meta"><span>90 events</span><span>30 questions</span><span>Codex CLI</span><span>top-k 5</span><span>run observed 2026-08-06</span></div>
</div></header>
<main class="shell">
<section class="summary"><div class="eyebrow">Readout</div><div class="summary-grid">
<div class="summary-item"><span class="summary-label">Highest audited accuracy</span><span class="summary-value">Selective memory · 96.7%</span><span class="summary-label">29 / 30 correct</span></div>
<div class="summary-item"><span class="summary-label">Lowest token proxy</span><span class="summary-value">Large context · 9,085</span><span class="summary-label">estimated total tokens</span></div>
<div class="summary-item"><span class="summary-label">Fastest observed run</span><span class="summary-value">TF-IDF RAG · 108.809s</span><span class="summary-label">one replay, not a latency guarantee</span></div>
</div></section>

<section class="panel"><div class="eyebrow">01 / accuracy</div><h2>Audited accuracy is the headline; automated labels stay visible.</h2><p>Manual review covered every non-Correct automated row. The audited score counts only fully correct answers. No cost or time weighting is used.</p><div class="chart">{svg_accuracy(methods)}</div>
<table aria-label="Accuracy comparison"><thead><tr><th>Approach</th><th>Audited</th><th>Automated rubric</th><th>Audited outcomes</th></tr></thead><tbody>{method_rows}</tbody></table></section>

<div class="grid"><section class="panel span-6"><div class="eyebrow">02 / outcome mix</div><h2>What the accuracy number contains</h2><p>Partial answers are kept separate from incorrect answers instead of being silently folded into a single error bucket.</p><div class="chart">{svg_outcomes(methods)}</div></section>
<section class="panel span-6"><div class="eyebrow">03 / retrieval</div><h2>RAG coverage is not RAG correctness.</h2><p>Top-five TF-IDF retrieval found at least one current supporting event for {coverage["any_supporting_event"]}/30 questions.</p><div class="chart">{svg_coverage(coverage)}</div></section></div>

<section class="panel"><div class="eyebrow">04 / tradeoff</div><h2>Lower proxy cost does not imply lower wall time.</h2><p>This plot is descriptive for one replay. The x-axis is an estimated total token-cost proxy, not USD; the y-axis is observed end-to-end wall time. Lower-left is cheaper and faster, but accuracy is labeled independently.</p><div class="chart">{svg_tradeoff(methods)}</div>
<div class="callout"><strong>Metric-specific conclusion.</strong> Selective memory has the highest audited accuracy and uses 18.1% fewer estimated total tokens than traditional RAG, while its observed replay is 99.7% slower. Traditional RAG is fastest. There is no single composite winner.</div>
<table aria-label="Cost and time comparison"><thead><tr><th>Approach</th><th>Input proxy</th><th>Output proxy</th><th>Total proxy</th><th>Observed time</th><th>vs TF-IDF RAG</th></tr></thead><tbody>
{''.join(f'<tr><th scope="row">{esc(m["name"])}</th><td>{m["input_token_proxy"]:,}</td><td>{m["output_token_proxy"]:,}</td><td>{m["total_token_proxy"]:,}</td><td>{m["wall_seconds"]:.3f}s</td><td>{("baseline" if m["name"] == "Traditional TF-IDF RAG" else f"{((m["total_token_proxy"] / next(x["total_token_proxy"] for x in methods if x["name"] == "Traditional TF-IDF RAG") - 1) * 100):+.1f}% tokens; {((m["wall_seconds"] / WALL_SECONDS["Traditional TF-IDF RAG"] - 1) * 100):+.1f}% time")}</td></tr>' for m in methods)}
</tbody></table><p class="panel-note">Exact billable USD is intentionally not asserted: this Codex replay did not expose a model price schedule or invoice-level usage. Apply a known input/output rate to the saved proxy counts if a USD estimate is required.</p></section>

<div class="grid"><section class="panel span-6"><div class="eyebrow">05 / error profile</div><h2>Where answers still fail</h2><p>Counts below use the audited categories, not the automated keyword error labels.</p><div class="chart">{svg_errors(methods)}</div></section>
<section class="panel span-6"><div class="eyebrow">06 / selective memory</div><h2>Selective-memory wins and miss</h2><p>Selective memory was the only highest-scoring approach on <code>{", ".join(snapshot["selective_wins"])}</code>. Its remaining miss is an event-provenance error on Q23: the answer cited nearby keyboard-coverage events instead of E081 and E086.</p><div class="callout"><strong>Interpretation.</strong> The result supports a bounded claim about this fictional 90-event dataset and this replay. It does not establish general superiority across models, datasets, or repeated trials.</div></section></div>

<section class="panel"><div class="eyebrow">07 / question-level audit</div><h2>Every question, same rubric</h2><p>Legend: C = correct, P = partially correct, I = incorrect. The winner column uses the audited labels and a strict ordinal ranking.</p><div class="matrix-wrap"><table aria-label="Question-level audited status"><thead><tr><th>Q</th><th>Question</th><th>Large</th><th>RAG</th><th>Selective</th><th>Highest label</th></tr></thead><tbody>{matrix_rows}</tbody></table></div></section>
</main>
<footer><div class="shell">Built from saved repository artifacts with inline SVG and semantic HTML. Visual direction follows <a href="https://vercel.com/design.md">Vercel design guidance</a>; no chart library or third-party runtime is required. Source files: <code>results/week7_final_scoring.csv</code>, <code>results/week7_summary.md</code>.</div></footer>
</body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Build and validate in memory without writing files")
    args = parser.parse_args()
    snapshot = build_snapshot()
    report = render_report(snapshot)
    if args.check:
        assert "Accuracy, cost, and time" in report
        assert "Estimated total token-cost proxy" in report
        assert report.count("Question-level audited status") == 1
        print("Validated snapshot and rendered report in memory.")
        return
    (OUT / "benchmark_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    (OUT / "index.html").write_text(report, encoding="utf-8")
    print("Wrote visual_benchmark/benchmark_snapshot.json and visual_benchmark/index.html")


if __name__ == "__main__":
    main()
