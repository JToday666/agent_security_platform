import unittest

from app.models.benchmark import RiskCategory, RiskSubtypeDisplayMeta
from app.models.benchmark_run import SampleExecution, TestRun


class SchemaModelTestCase(unittest.TestCase):
    def test_risk_category_has_display_columns(self) -> None:
        self.assertIn("meaning", RiskCategory.__table__.c)
        self.assertIn("updated_at", RiskCategory.__table__.c)

    def test_risk_subtype_display_meta_exists(self) -> None:
        columns = RiskSubtypeDisplayMeta.__table__.c
        self.assertIn("subtype_id", columns)
        self.assertIn("short_description", columns)
        self.assertIn("full_description", columns)
        self.assertIn("highlights", columns)
        self.assertIn("scenarios", columns)
        self.assertIn("resources", columns)
        self.assertIn("media", columns)
        self.assertIn("updated_at", columns)

    def test_test_run_has_public_interface_columns(self) -> None:
        columns = TestRun.__table__.c
        self.assertIn("public_id", columns)
        self.assertIn("agent_name", columns)
        self.assertIn("description", columns)
        self.assertIn("submit_method", columns)
        self.assertIn("public_to_leaderboard", columns)
        self.assertIn("request_id", columns)
        self.assertIn("updated_at", columns)
        self.assertIn("finalization_reason", columns)

    def test_sample_execution_has_updated_at(self) -> None:
        self.assertIn("updated_at", SampleExecution.__table__.c)


if __name__ == "__main__":
    unittest.main()
