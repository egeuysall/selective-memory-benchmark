# Week 6 RAG vs Selective-Memory Efficiency

Measured on 2026-08-06 with the same 30 questions, Codex CLI path, and
`--top-k 5` setting. Each value is one fresh live replay, so wall time is
observational rather than a stable service-level benchmark.

## Measured comparison

| Metric | Traditional TF-IDF RAG | Selective memory | Selective-memory change vs RAG |
| --- | ---: | ---: | ---: |
| Prompt characters | 58,503 | 47,380 | -11,123 (-19.0%) |
| Estimated input tokens* | 14,626 | 11,845 | -2,781 (-19.0%) |
| Answer characters | 2,469 | 2,585 | +116 (+4.7%) |
| Estimated output tokens* | 618 | 647 | +29 (+4.7%) |
| Estimated total tokens* | 15,244 | 12,492 | -2,752 (-18.1%) |
| End-to-end wall time | 108.809 s | 217.326 s | +108.517 s (+99.7%); 2.0x slower |
| Correct answers | 21/30 | 25/30 | +4 answers; +13.3 percentage points |

*Token estimates use `ceil(character_count / 4)`. They are a transparent cost
proxy, not billable usage. The local Codex runner did not expose an invoice or
token-price record, so exact dollar costs are not asserted. Given the same
model and price schedule, the measured prompt proxy implies approximately 19.0%
lower input cost and 18.1% lower combined input/output token cost for selective
memory in this replay. To convert to dollars, apply the model's input and
output rates to the two token counts.

## What the result means

Selective memory used a smaller prompt and scored higher in this replay, but it
was slower end-to-end. The latency result is not contradictory: model service
latency, generation length, and run-to-run variance can dominate the reduction
in prompt size. The safe conclusion is that selective memory reduced the token
cost proxy; this one replay does not prove a speed improvement.

RAG retrieval quality remained separately measurable: the top five contained at
least one current supporting event for 28/30 questions and the complete
supporting-event set for 23/30.

## Reproduce the timing

```bash
python3 - <<'PY'
import subprocess, sys, time
for mode in ("rag", "selective"):
    start = time.perf_counter()
    subprocess.run(
        [sys.executable, "src/benchmark.py", "run", "--mode", mode,
         "--engine", "codex", "--top-k", "5"],
        check=True,
    )
    print(mode, round(time.perf_counter() - start, 3), "seconds")
PY
```
