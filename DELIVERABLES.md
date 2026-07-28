# RecallBench

## Evaluating AI Memory for Long-Term Project Support

RecallBench is the Week 4 and Week 5 submission for the research project
originally proposed as *Selective Memory in AI Agents: A Benchmark for
Long-Term Project Support*. It evaluates whether an AI answers long-term
project questions more accurately when it receives the complete project
history or a smaller set of updates selected by retrieval.

## Submission links

- [Public GitHub repository](https://github.com/egeuysall/selective-memory-benchmark)
- [Public Week 3 Google Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vShzbDGNay0SFVU8jsFeOO9Xr_NNcNiKUxvRHrRnYnJBZkybYBQs2o0X3mJe8akU0riTyxe6lF2_Exh/pubhtml)
- [Week 4 result CSV](results/week4_large_context_results.csv)
- [Week 5 result CSV](results/week5_rag_results.csv)
- [Approach comparison CSV](results/comparison.csv)
- [Five-Minute Feedback Form](https://tinyurl.com/5minstudentfeedbackform)

## Dataset and fictional project

The experiment uses the fictional ShieldPath Learning Lab dataset created in
Week 3. ShieldPath is a privacy-first learning platform with courses, quizzes,
browser exercises, locally stored learner progress, and release-quality gates.
The dataset contains 86 events over 30 consecutive days. It includes current
and former task owners, completed and delayed work, active and resolved
blockers, changed deadlines, canceled features, and technical decisions that
were later replaced.

The timeline was inspired by realistic activity from a student software
project and transformed into a fictional benchmark. It does not claim that the
fictional events literally occurred in the source repository. No passwords,
tokens, contact details, private messages, or other sensitive information are
included.

## Research question

Does providing an AI with the full 30-day project history improve its answers,
or does the additional outdated and irrelevant information make accurate
project recall more difficult?

## Evaluation design

The same 15 questions were used for both approaches. They test current owners,
completed tasks, delayed tasks, active and resolved blockers, current
requirements, removed features, changed deadlines, and conflicts between older
and newer information.

The large-context baseline received all 86 updates in one prompt. The RAG
baseline represented every project update as a short document, ranked the
documents with TF-IDF cosine similarity, and supplied the five highest-ranking
updates for each question. Both approaches used the same answering
instructions and the same evaluation rubric.

Answers were labeled:

- **Correct** when the current fact and required details were present
- **Incomplete** when part of the answer was correct but required information
  was missing
- **Incorrect** when the answer was wrong or relied on an outdated fact

Tracked error types were incomplete answer, outdated information error, wrong
task owner, missed blocker, missed requirement change, irrelevant retrieved
information, and not enough information retrieved.

# Week 4 Deliverable

## Large-context baseline and evaluation questions

The model received all 86 project events at once. Each answer below was checked
against the Day 30 project state and the supporting event chain.

| ID | Question | Correct Answer | Large-Context AI Answer | Result | Error Type | Notes |
|---|---|---|---|---|---|---|
| Q01 | Who currently owns the browser smoke tests? | Shaurya | Shaurya. | Correct | Correct | Rejected the older Ishaan assignment. |
| Q02 | Which project tasks are delayed at the end of Day 30? | MVP release and legacy accessibility cleanup | The MVP release and legacy accessibility cleanup. | Correct | Correct | Did not treat previously delayed guided paths as currently delayed. |
| Q03 | What is the only active blocker at the end of Day 30? | Incomplete keyboard-only smoke coverage | Incomplete keyboard-only smoke coverage for core catalog and terminal controls. | Correct | Correct | Ignored earlier resolved blockers. |
| Q04 | What is the current MVP release target? | July 17, 2026 | July 17, 2026. | Correct | Correct | Used the revised date rather than July 13. |
| Q05 | Which planned feature was removed because an existing mock mode already covered the need? | Standalone terminal demo mode | Standalone terminal demo mode. | Correct | Correct | Identified the canceled duplicate feature. |
| Q06 | Is the Live Help offline fallback still part of the current MVP? | No. It was canceled and removed from the current MVP. | No. It was removed from the current MVP and retained in the future backlog. | Correct | Correct | Did not treat the old planned state as current. |
| Q07 | Which browser testing framework is the current technical decision? | Playwright | Playwright. | Correct | Correct | Rejected the earlier Cypress decision. |
| Q08 | Which cloud platform is the current primary terminal deployment target? | Azure VM | Microsoft Azure VM. | Correct | Correct | Rejected the earlier OCI-first plan. |
| Q09 | What is the current terminal draft recovery requirement? | Visible recovered state, confirmed discard, and challenge-scoped storage | Challenge-scoped draft persistence with a visible recovered state and confirmed discard control. | Correct | Correct | Rejected silent-only recovery. |
| Q10 | Who owns guided learning paths and what is their current status? | Aryan Raj, completed | Aryan Raj; completed. | Correct | Correct | Rejected Ashwin’s former ownership and delayed status. |
| Q11 | What is the current status of the static HTML QA gate? | Completed | Completed and merged. | Correct | Correct | Rejected former blocked and under-review states. |
| Q12 | What rules define the current static HTML QA gate? | Check changed files, ignore HTML comments, and use a small explicit allowlist | It checks changed HTML only, strips HTML comments, and uses a small explicit allowlist. | Correct | Correct | Correctly summarized the final requirement changes. |
| Q13 | Who owns local learner progress and is it complete? | Aarohi, completed | Aarohi; yes, it is complete. | Correct | Correct | Rejected Advay’s former ownership. |
| Q14 | Is root deployment routing still blocking the project? | No. It was resolved and completed. | No. Root and subpath routing now use one safe resolver, and the fix is complete. | Correct | Correct | Recognized a resolved blocker. |
| Q15 | Which README approach should be ignored as outdated? | The long, badge-heavy, presentation-focused draft | The long, badge-heavy, presentation-heavy README with multiple screenshots and a detailed contributor guide. | Correct | Correct | Selected the outdated approach rather than the concise final README. |

## Week 4 result

| Metric | Value |
|---|---:|
| Questions | 15 |
| Correct | 15 |
| Incomplete | 0 |
| Incorrect | 0 |
| Accuracy | 100% |

## Week 4 meeting recap

The questions cover all required memory categories and deliberately place
current facts beside conflicting older facts. The large-context baseline
answered every question correctly. This suggests that, for an 86-event
timeline with explicit dates and validity information, the model could resolve
ownership changes, requirement changes, and canceled work even when the full
history was present. The result does not prove that large context is always
better because the dataset is still small enough to fit comfortably in one
prompt.

# Week 5 Deliverable

## TF-IDF RAG baseline

The RAG system searched all 86 events separately for every question. It used
term frequency-inverse document frequency and cosine similarity to return the
top five events. Only those retrieved events were supplied to the answering
model.

| ID | Question | Correct Answer | Top Five Retrieved Events | RAG Answer | Result | Error Type | Comparison Note |
|---|---|---|---|---|---|---|---|
| Q01 | Who currently owns the browser smoke tests? | Shaurya | E008, E002, E020, E013, E017 | Shaurya. | Correct | Correct | Retrieval included old and new owners; the model selected the latest one. |
| Q02 | Which project tasks are delayed at the end of Day 30? | MVP release and legacy accessibility cleanup | E086, E060, E085, E050, E009 | Legacy accessibility cleanup and MVP release. | Correct | Correct | The model ignored the outdated guided-path delay in E060. |
| Q03 | What is the only active blocker at the end of Day 30? | Incomplete keyboard-only smoke coverage | E086, E009, E051, E050, E049 | Incomplete keyboard-only smoke coverage. | Correct | Correct | Older analytics blockers were retrieved but not treated as current. |
| Q04 | What is the current MVP release target? | July 17, 2026 | E009, E085, E081, E045, E034 | July 17, 2026. | Correct | Correct | Both deadline versions were retrieved; the revised one won. |
| Q05 | Which planned feature was removed because an existing mock mode already covered the need? | Standalone terminal demo mode | E035, E007, E045, E002, E019 | Standalone terminal demo mode. | Correct | Correct | The removal and original proposal were both available. |
| Q06 | Is the Live Help offline fallback still part of the current MVP? | No. It was canceled and removed. | E045, E005, E029, E041, E002 | No. It was removed from the current MVP and moved to the future backlog. | Correct | Correct | The cancellation outranked the older planned and blocked states. |
| Q07 | Which browser testing framework is current? | Playwright | E003, E014, E008, E037, E017 | Playwright. | Correct | Correct | Both Cypress and Playwright appeared; the replacement event resolved the conflict. |
| Q08 | Which cloud platform is the primary terminal deployment target? | Azure VM | E034, E025, E040, E036, E009 | An Azure VM. | Correct | Correct | Both OCI and Azure were retrieved; Azure was correctly selected. |
| Q09 | What is the current terminal draft recovery requirement? | Visible recovered state, confirmed discard, and challenge-scoped storage | E050, E001, E022, E021, E047 | Challenge-scoped draft persistence with a visible recovered state and confirmed discard control. | Correct | Correct | The model rejected silent-only recovery from E021. |
| Q10 | Who owns guided learning paths and what is their status? | Aryan Raj, completed | E076, E052, E060, E074, E070 | Aryan Raj; completed. | Correct | Correct | Old planned, delayed, and blocked states did not override completion. |
| Q11 | What is the status of the static HTML QA gate? | Completed | E078, E069, E066, E054, E071 | Completed. | Correct | Correct | The latest completion event resolved older review and blocker states. |
| Q12 | What rules define the current static HTML QA gate? | Changed files, ignored comments, and a small allowlist | E078, E069, E066, E054, E071 | Run on changed HTML only, strip commented markup, and use a small explicit allowlist. | Correct | Correct | Retrieval contained the requirement-change sequence. |
| Q13 | Who owns local learner progress and is it complete? | Aarohi, completed | E023, E031, E026, E012, E050 | Aarohi; yes, it is complete. | Correct | Correct | The old Advay assignment was retrieved but ignored. |
| Q14 | Is root deployment routing still blocking the project? | No. It was resolved and completed. | E038, E033, E025, E036, E040 | No. It is resolved and completed. | Correct | Correct | The blocked and resolved routing events were both retrieved. |
| Q15 | Which README approach should be ignored? | The long, badge-heavy, presentation-focused draft | E067, E063, E058, E006, E059 | The long, badge-heavy, presentation-focused README with multiple screenshots and a detailed contributor guide. | Correct | Correct | The full README change chain was retrieved. |

The complete retrieved event text and similarity scores are preserved in
[`results/week5_rag_results.csv`](results/week5_rag_results.csv).

## Week 5 result

| Metric | Value |
|---|---:|
| Questions | 15 |
| Updates retrieved per question | 5 |
| Correct | 15 |
| Incomplete | 0 |
| Incorrect | 0 |
| Accuracy | 100% |

## Week 5 meeting recap

The retrieved updates were useful because every question received at least one
event containing the current answer. In several cases, retrieval also returned
an older conflicting event. The answering model still chose the newer fact.
RAG matched the large-context baseline at 100% accuracy, so this experiment
does not show an accuracy improvement from reducing context. It does show that
TF-IDF reduced the supplied history from 86 events to five events per question
without losing answer quality.

# Comparison and Conclusion

| Approach | Context Supplied | Correct | Incomplete | Incorrect | Accuracy |
|---|---|---:|---:|---:|---:|
| Large context | All 86 updates | 15 | 0 | 0 | 100% |
| TF-IDF RAG | Top 5 updates per question | 15 | 0 | 0 | 100% |

Neither approach performed better on this first test. Large context retained
all possible evidence but required the model to process the entire history.
TF-IDF RAG used much less context and preserved accuracy, although it sometimes
retrieved both current and outdated facts. This means the retrieval stage
reduced input size but did not completely solve temporal conflict.

The most important next comparison is selective memory. A selective-memory
system could keep the latest owner, status, requirement, blocker, and deadline
as compact current state while retaining links to historical evidence. It may
perform differently because it would avoid presenting superseded facts unless
a historical question required them.

## Limitations

- This was one recorded run with one answering model.
- The dataset contains explicit event dates, replacement links, and validity
  labels, which make temporal reasoning easier.
- TF-IDF matches words rather than meaning and may perform worse on paraphrased
  questions.
- The transparent keyword rubric was manually checked against the saved model
  answers, but larger studies should use independent graders or repeated runs.
- A perfect score does not show that both methods will remain equal on longer,
  noisier, or less structured project histories.

## Reproduction

Requirements are Python 3.11 or newer and an authenticated Codex CLI.

```bash
git clone https://github.com/egeuysall/selective-memory-benchmark.git
cd selective-memory-benchmark
python3 src/benchmark.py validate
python3 -m unittest discover -s tests -v
python3 src/benchmark.py run --mode all --engine codex --top-k 5
```

The implementation uses only the Python standard library. The recorded raw
answers, retrieved updates, scores, and comparison tables are committed to the
repository.

## Submission checklist

- [x] 15 evaluation questions with correct answers
- [x] Questions cover owners, completed work, delays, blockers, requirements,
  contradictions, and canceled information
- [x] Large-context baseline tested with all 86 project events
- [x] Large-context answers graded and documented
- [x] TF-IDF retrieval baseline implemented outside Google Colab
- [x] Five updates retrieved for every question
- [x] RAG answers graded and documented
- [x] Both approaches compared
- [x] Error types tracked
- [x] Meeting recap discussion included
- [x] Reproduction instructions included
- [x] Public Week 3 dataset and public source repository linked
- [x] No sensitive information included
