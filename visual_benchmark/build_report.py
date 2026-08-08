#!/usr/bin/env python3
"""Generate one Vercel-style SVG from the current automated benchmark files."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import benchmark  # noqa: E402

CONDITIONS = (
    ("Large context", "large", "week6_large_context_results.csv", "AI Answer", "week6_large_raw.json", "circle"),
    ("Traditional TF-IDF RAG", "rag", "week6_rag_results.csv", "RAG Answer", "week6_rag_raw.json", "square"),
    ("Selective memory", "selective", "week6_selective_memory_results.csv", "Selective-Memory Answer", "week6_selective_raw.json", "triangle"),
)
RUN_METRICS = RESULTS / "benchmark_run_metrics.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def ceil_tokens(characters: int) -> int:
    return math.ceil(characters / 4)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_metrics() -> dict:
    if not RUN_METRICS.exists():
        return {"engine": "unknown", "top_k": 5, "mode": "unknown", "conditions": {}}
    return json.loads(RUN_METRICS.read_text(encoding="utf-8"))


def build_snapshot() -> dict:
    events = benchmark.read_csv(benchmark.DATA / "project_updates.csv")
    questions = benchmark.read_csv(benchmark.DATA / "evaluation_questions.csv")
    current_state = benchmark.read_csv(benchmark.DATA / "day30_current_state.csv")
    memory = benchmark.build_selective_memory(events, current_state)
    metrics = load_metrics()
    top_k = metrics.get("top_k", 5)
    contexts = {
        row["Question ID"]: benchmark.retrieve(row["Question"], events, top_k)
        for row in questions
    }
    prompts = {
        "large": benchmark.large_context_prompt(events, questions),
        "rag": benchmark.rag_prompt(questions, contexts),
        "selective": benchmark.selective_memory_prompt(questions, memory),
    }
    methods = []
    for name, key, result_name, answer_field, raw_name, shape in CONDITIONS:
        rows = read_csv(RESULTS / result_name)
        raw = json.loads((RESULTS / raw_name).read_text(encoding="utf-8"))
        answer_chars = sum(len(answer["answer"]) for answer in raw["answers"])
        prompt_chars = len(prompts[key])
        timing = metrics.get("conditions", {}).get(key, {})
        methods.append({
            "name": name,
            "key": key,
            "shape": shape,
            "questions": len(rows),
            "correct": sum(row["Correct/Incorrect"] == "Correct" for row in rows),
            "incomplete": sum(row["Correct/Incorrect"] == "Incomplete" for row in rows),
            "incorrect": sum(row["Correct/Incorrect"] == "Incorrect" for row in rows),
            "prompt_chars": prompt_chars,
            "input_token_proxy": ceil_tokens(prompt_chars),
            "answer_chars": answer_chars,
            "output_token_proxy": ceil_tokens(answer_chars),
            "total_token_proxy": ceil_tokens(prompt_chars) + ceil_tokens(answer_chars),
            "wall_seconds": timing.get("wall_seconds"),
            "timing_source": timing.get("source", "saved run metrics"),
        })

    rag_rows = read_csv(RESULTS / "week6_rag_results.csv")
    coverage = {
        "any": sum(row["Supporting Event Retrieved"] == "Yes" for row in rag_rows),
        "all": sum(row["Supporting Event Coverage"] == "All" for row in rag_rows),
        "partial": sum(row["Supporting Event Coverage"] == "Partial" for row in rag_rows),
        "none": sum(row["Supporting Event Coverage"] == "None" for row in rag_rows),
    }
    snapshot = {
        "title": "Accuracy against estimated token cost",
        "source": "Automated labels from the current Week 6 result CSVs",
        "run": {
            "engine": metrics.get("engine", "unknown"),
            "mode": metrics.get("mode", "unknown"),
            "top_k": metrics.get("top_k", 5),
            "recorded_at": metrics.get("recorded_at"),
            "events": len(events),
            "questions": len(questions),
        },
        "methods": methods,
        "rag_coverage": coverage,
        "notes": [
            "Accuracy is automated Correct answers divided by 30.",
            "Cost is an estimated total token proxy using ceil(characters / 4), not USD.",
            "Time is one observed end-to-end run per condition when available.",
            "The graph has no composite score. Metric-specific tradeoffs remain visible.",
        ],
    }
    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot: dict) -> None:
    assert snapshot["run"]["events"] == 90
    assert snapshot["run"]["questions"] == 30
    assert len(snapshot["methods"]) == 3
    assert all(method["questions"] == 30 for method in snapshot["methods"])
    assert all(method["total_token_proxy"] > 0 for method in snapshot["methods"])
    assert snapshot["rag_coverage"]["any"] == 28
    assert snapshot["rag_coverage"]["all"] == 23
    assert snapshot["rag_coverage"]["partial"] == 5
    assert snapshot["rag_coverage"]["none"] == 2


def pct(correct: int, total: int) -> str:
    return f"{correct / total * 100:.1f}%"


def time_text(seconds: float | None) -> str:
    return f"{seconds:.3f}s" if seconds is not None else "time n/a"


def text(x: float, y: float, value: str, class_name: str, anchor: str = "start") -> str:
    return f'<text class="{class_name}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{esc(value)}</text>'


def marker(method: dict, x: float, y: float) -> str:
    shape = method["shape"]
    if shape == "square":
        return f'<rect class="mark open" x="{x - 7:.1f}" y="{y - 7:.1f}" width="14" height="14" />'
    if shape == "triangle":
        return f'<path class="mark filled" d="M {x:.1f} {y - 9:.1f} L {x + 9:.1f} {y + 8:.1f} L {x - 9:.1f} {y + 8:.1f} Z" />'
    return f'<circle class="mark filled" cx="{x:.1f}" cy="{y:.1f}" r="7" />'


def render_svg(snapshot: dict) -> str:
    width, height = 1200, 800
    left, right, top, bottom = 116, 76, 188, 540
    plot_w, plot_h = width - left - right, bottom - top
    methods = snapshot["methods"]
    max_cost = max(method["total_token_proxy"] for method in methods)
    x_max = max_cost * 1.18

    def x_position(cost: int) -> float:
        return left + plot_w * cost / x_max

    def y_position(accuracy: float) -> float:
        return bottom - plot_h * accuracy

    parts = [
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-description">
<title id="chart-title">{esc(snapshot["title"])}</title>
<desc id="chart-description">One point per benchmark condition. The vertical axis is automated accuracy. The horizontal axis is estimated total token cost. Each point label includes observed wall time. Lower left means lower cost and faster time, but there is no composite score.</desc>
<style>
  text {{ font-family: Geist, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111; }}
  .mono {{ font-family: Geist Mono, ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .eyebrow {{ font-size: 12px; letter-spacing: 1.4px; fill: #666; }}
  .title {{ font-size: 34px; font-weight: 600; letter-spacing: -1.4px; }}
  .subtitle {{ font-size: 14px; fill: #666; }}
  .axis-title {{ font-size: 12px; fill: #666; }}
  .tick {{ font-size: 12px; fill: #666; }}
  .label {{ font-size: 14px; font-weight: 600; }}
  .detail {{ font-size: 12px; fill: #666; }}
  .note {{ font-size: 12px; fill: #666; }}
  .grid {{ stroke: #eaeaea; stroke-width: 1; }}
  .axis {{ stroke: #111; stroke-width: 1.2; }}
  .leader {{ stroke: #999; stroke-width: 1; fill: none; }}
  .mark {{ stroke: #111; stroke-width: 2; }}
  .mark.filled {{ fill: #111; }}
  .mark.open {{ fill: #fff; }}
  .hairline {{ stroke: #111; stroke-width: 1; }}
</style>
<rect width="{width}" height="{height}" fill="#fff" />
{text(84, 60, "RECALLBENCH", "eyebrow")}
{text(84, 104, "Accuracy against estimated token cost", "title")}
{text(84, 130, f"90 events / 30 questions / {snapshot['run']['engine']} / top-k {snapshot['run']['top_k']}", "subtitle")}
<line class="hairline" x1="{left}" y1="{top - 36}" x2="{width - right}" y2="{top - 36}" />
'''
    ]

    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = y_position(tick)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" />')
        parts.append(text(left - 16, y + 4, f"{tick * 100:.0f}%", "tick mono", "end"))
    for tick in (0, 5000, 10000, 15000):
        if tick > x_max:
            continue
        x = x_position(tick)
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" />')
        parts.append(text(x, bottom + 24, f"{tick // 1000}k" if tick else "0", "tick mono", "middle"))
    parts += [
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" />',
        f'<line class="axis" x1="{left}" y1="{bottom}" x2="{left + plot_w}" y2="{bottom}" />',
        text(left, top - 12, "Automated accuracy", "axis-title"),
        text(left + plot_w / 2, bottom + 50, "Estimated total token-cost proxy, lower is cheaper", "axis-title", "middle"),
    ]

    label_positions = {
        "large": (-24, -64, "end"),
        "rag": (-24, 60, "end"),
        "selective": (28, -70, "start"),
    }
    for method in methods:
        accuracy = method["correct"] / method["questions"]
        x = x_position(method["total_token_proxy"])
        y = y_position(accuracy)
        dx, dy, anchor = label_positions[method["key"]]
        label_x = x + dx
        label_y = y + dy
        line_end_x = label_x + (7 if anchor == "start" else -7)
        line_end_y = label_y + (4 if dy < 0 else -20)
        parts.append(f'<path class="leader" d="M {x:.1f} {y:.1f} L {line_end_x:.1f} {line_end_y:.1f}" />')
        parts.append(marker(method, x, y))
        parts.append(text(label_x, label_y, method["name"], "label", anchor))
        parts.append(text(label_x, label_y + 20, f"{method['correct']}/30 / {pct(method['correct'], method['questions'])} / {method['total_token_proxy']:,} tokens", "detail mono", anchor))
        parts.append(text(label_x, label_y + 39, time_text(method["wall_seconds"]), "detail mono", anchor))

    legend_x = left + plot_w - 410
    legend_y = 130
    for index, method in enumerate(methods):
        x = legend_x + index * 142
        parts.append(marker(method, x, legend_y - 4))
        parts.append(text(x + 16, legend_y, method["name"].replace("Traditional TF-IDF ", "TF-IDF "), "detail"))

    rag = next(method for method in methods if method["key"] == "rag")
    selective = next(method for method in methods if method["key"] == "selective")
    token_delta = (selective["total_token_proxy"] / rag["total_token_proxy"] - 1) * 100
    selective_time = selective["wall_seconds"]
    rag_time = rag["wall_seconds"]
    time_delta = ((selective_time / rag_time) - 1) * 100 if selective_time is not None and rag_time else None
    time_note = f"{time_delta:.1f}% slower than RAG" if time_delta is not None else "time unavailable"
    parts += [
        '<line class="hairline" x1="116" y1="620" x2="1124" y2="620" />',
        text(116, 650, "Metric-specific readout", "eyebrow"),
        text(116, 676, f"Selective memory: {pct(selective['correct'], selective['questions'])} accuracy / {abs(token_delta):.1f}% lower token proxy than RAG / {time_note}", "note mono"),
        text(116, 700, "RAG is fastest. Exact USD is unavailable from this replay. No composite score is used.", "note"),
        text(1124, 744, "Accuracy = automated Correct / 30. Cost = ceil(characters / 4). Time = one observed run.", "note mono", "end"),
        text(1124, 768, "Source: current results/week6_* CSVs and benchmark_run_metrics.json", "note mono", "end"),
        '</svg>',
    ]
    svg = "".join(parts)
    assert "\u2014" not in svg
    return svg


def write_artifacts() -> dict:
    snapshot = build_snapshot()
    svg = render_svg(snapshot)
    (OUT / "benchmark_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    (OUT / "benchmark.svg").write_text(svg + "\n", encoding="utf-8")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate the current automated SVG without writing it")
    args = parser.parse_args()
    snapshot = build_snapshot()
    svg = render_svg(snapshot)
    if args.check:
        assert svg.startswith("<svg ")
        assert svg.count("<title") == 1
        assert svg.count("<desc") == 1
        assert svg.count('class="mark') == 6
        assert "Accuracy against estimated token cost" in svg
        assert "<html" not in svg.lower()
        print("Validated one automated benchmark SVG.")
        return
    (OUT / "benchmark_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    (OUT / "benchmark.svg").write_text(svg + "\n", encoding="utf-8")
    print("Wrote visual_benchmark/benchmark.svg and benchmark_snapshot.json")


if __name__ == "__main__":
    main()
