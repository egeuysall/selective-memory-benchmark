import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from benchmark import classify, read_csv, retrieve  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
