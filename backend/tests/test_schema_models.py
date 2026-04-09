import unittest

from app.models.benchmark import RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta, SampleOracle
from app.models.benchmark_run import RunDataset, SampleExecution, TestRun


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
        self.assertIn("pause_used", columns)
        self.assertIn("pause_deadline_at", columns)
        self.assertIn("requested_action", columns)
        self.assertIn("requested_action_at", columns)
        self.assertIn("claimed_by", columns)
        self.assertIn("claimed_at", columns)
        self.assertIn("claim_heartbeat_at", columns)

    def test_test_run_has_pause_timeout_lookup_index(self) -> None:
        indexes = {
            index.name: tuple(column.name for column in index.columns)
            for index in TestRun.__table__.indexes
        }
        self.assertIn("ix_test_runs_status_pause_deadline_at", indexes)
        self.assertEqual(
            ("status", "pause_deadline_at"),
            indexes["ix_test_runs_status_pause_deadline_at"],
        )

    def test_sample_execution_has_updated_at(self) -> None:
        self.assertIn("updated_at", SampleExecution.__table__.c)

    def test_run_dataset_model_exists(self) -> None:
        columns = RunDataset.__table__.c
        self.assertIn("run_id", columns)
        self.assertIn("dataset_code", columns)
        self.assertIn("dataset_name", columns)
        self.assertIn("order_no", columns)
        self.assertIn("status", columns)
        self.assertIn("total_samples", columns)
        self.assertIn("completed_samples", columns)
        self.assertIn("created_at", columns)
        self.assertIn("updated_at", columns)
        self.assertIn("started_at", columns)
        self.assertIn("finished_at", columns)

    def test_risk_subtype_code_is_globally_unique(self) -> None:
        self.assertTrue(RiskSubtype.__table__.c.code.unique)

    def test_sample_oracle_updated_at_has_server_default(self) -> None:
        column = SampleOracle.__table__.c.updated_at
        self.assertIsNotNone(column.server_default)
        self.assertFalse(column.nullable)


if __name__ == "__main__":
    unittest.main()
