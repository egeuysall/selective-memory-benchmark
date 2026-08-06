import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from benchmark import (
    build_selective_memory,
    classify,
    read_csv,
    result_rows,
    retrieve,
)  # noqa: E402


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = read_csv(ROOT / "data" / "project_updates.csv")
        with (ROOT / "data" / "evaluation_questions.csv").open(
            newline="", encoding="utf-8-sig"
        ) as handle:
            cls.questions = list(csv.DictReader(handle))

    def test_retrieval_returns_ranked_events(self):
        results = retrieve("browser smoke tests owner", self.events, 5)
        self.assertEqual(len(results), 5)
        self.assertGreater(results[0][0], results[-1][0])
        self.assertTrue(all(result[1]["Event ID"].startswith("E") for result in results))

    def test_rubric_classifies_current_and_outdated_answers(self):
        question = self.questions[0]
        self.assertEqual(classify(question, "Shaurya"), ("Correct", "Correct"))
        self.assertEqual(
            classify(question, "Ishaan"),
            ("Incorrect", "Wrong task owner"),
        )
        self.assertEqual(
            classify(question, "Shaurya is current; Ishaan was the old owner."),
            ("Incorrect", "Wrong task owner"),
        )

    def test_selective_memory_marks_current_and_historical_facts(self):
        state = read_csv(ROOT / "data" / "day30_current_state.csv")
        memory = build_selective_memory(self.events, state)
        current = next(row for row in memory if row["Memory Item"] == "Browser smoke tests")
        old = next(
            row for row in memory
            if row["Memory Item"] == "Browser smoke tests"
            and row["Use or Ignore"] == "Ignore"
        )

        self.assertEqual(current["Use or Ignore"], "Use")
        self.assertIn("E020", current["Supporting Event IDs"])
        self.assertIn("Ishaan", old["Original Information"])
        self.assertEqual(old["Use or Ignore"], "Ignore")

    def test_rag_scoring_separates_current_event_retrieval_from_answer(self):
        question = self.questions[0]
        events_by_id = {event["Event ID"]: event for event in self.events}
        without_support = {
            "Q01": [(1.0, events_by_id[event_id]) for event_id in
                    ("E002", "E008", "E013", "E017", "E019")]
        }
        with_support = {
            "Q01": [(1.0, events_by_id[event_id]) for event_id in
                    ("E002", "E008", "E013", "E017", "E020")]
        }

        missing = result_rows([question], {"Q01": "Shaurya"}, without_support)[0]
        found = result_rows([question], {"Q01": "Shaurya"}, with_support)[0]

        self.assertEqual(missing["Supporting Event Retrieved"], "No")
        self.assertEqual(found["Supporting Event Retrieved"], "Yes")
        self.assertEqual(missing["Supporting Event Coverage"], "None")
        self.assertEqual(found["Supporting Event Coverage"], "All")
        self.assertEqual(missing["RAG Answer Correct"], "Yes")
        self.assertEqual(found["RAG Answer Correct"], "Yes")

        multi = self.questions[1]
        partial = result_rows(
            [multi],
            {"Q02": multi["Correct Answer"]},
            {"Q02": [(1.0, events_by_id["E090"])]},
        )[0]
        self.assertEqual(partial["Supporting Event Retrieved"], "Yes")
        self.assertEqual(partial["Supporting Event Coverage"], "Partial")


if __name__ == "__main__":
    unittest.main()
