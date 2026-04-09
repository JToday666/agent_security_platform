from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    BenchmarkSample,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    SampleOracle,
)
from app.modules.datasets.importer import apply_import_plan, build_import_plan, discover_legacy_sample_files
from app.shared.config import settings


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DEMO_ROOT = BACKEND_ROOT / "datasets_demo"


class DatasetsDemoImporterPlanTestCase(unittest.TestCase):
    def test_discover_legacy_sample_files_ignores_noise_json(self) -> None:
        sample_files = discover_legacy_sample_files(DATASETS_DEMO_ROOT)

        self.assertEqual(21, len(sample_files))
        self.assertTrue(all(path.name not in {"package.json", "package-lock.json", "default.json"} for path in sample_files))
        self.assertTrue(all("saved_logs" not in path.parts for path in sample_files))

    def test_build_import_plan_normalizes_browser_art_sample(self) -> None:
        plan = build_import_plan(DATASETS_DEMO_ROOT)

        sample = next(item for item in plan.samples if item.sample_id == "Browser-art_A5_1")
        self.assertEqual("browser_art", sample.dataset_source_code)
        self.assertEqual("direct_user_instruction", sample.attack_delivery_type_code)
        self.assertEqual("confidentiality", sample.risk_category_code)
        self.assertEqual("A5_credentials_and_secrets_leakage", sample.risk_subtype_code)
        self.assertEqual("api_keys_or_access_secrets_revealed_on_the_account_information_page", sample.asset_type_code)
        self.assertEqual("api_keys/index.html", sample.entry_path)
        self.assertEqual("Browser-art_A5_1", sample.sample_name)
        self.assertEqual(2, len([oracle for oracle in sample.oracles if oracle.oracle_kind == 1]))
        self.assertEqual(2, len([oracle for oracle in sample.oracles if oracle.oracle_kind == 2]))
        self.assertEqual(Decimal("0.675"), sample.difficulty_seed)
        self.assertEqual(Decimal("0.675"), sample.difficulty_score)

    def test_build_import_plan_uses_adv_html_fallback(self) -> None:
        plan = build_import_plan(DATASETS_DEMO_ROOT)

        sample = next(item for item in plan.samples if item.sample_id == "EIA_A1_1_high")
        self.assertEqual("adv_modified_file_action_grounding_form_type2_near_bot_1.html", sample.entry_path)
        self.assertEqual("A1_identity_leakage", sample.risk_subtype_code)

    def test_build_import_plan_prefers_goal_path_before_other_candidates(self) -> None:
        plan = build_import_plan(DATASETS_DEMO_ROOT)

        sample = next(item for item in plan.samples if item.sample_id == "VPI-bench_B2_1_high")
        self.assertEqual("amazon/index.html", sample.entry_path)
        self.assertEqual("vpi_bench", sample.dataset_source_code)
        self.assertEqual("B2_cloud_file_modification", sample.risk_subtype_code)
        self.assertEqual(Decimal("1.000"), sample.difficulty_seed)

    def test_import_script_exists_and_supports_help(self) -> None:
        script_path = BACKEND_ROOT / "scripts" / "import_datasets_demo.py"
        self.assertTrue(script_path.exists())

        spec = importlib.util.spec_from_file_location("import_datasets_demo", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Import dataset demo samples into the database", result.stdout)


class DatasetsDemoImporterDatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(settings.SYNC_DATABASE_URL, future=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection, future=True)

    def tearDown(self) -> None:
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    def test_apply_import_plan_is_idempotent_and_updates_existing_rows(self) -> None:
        plan = self._with_prefix(build_import_plan(DATASETS_DEMO_ROOT), "test_importer")

        first_result = apply_import_plan(self.session, plan)
        self.assertEqual(21, first_result.created_samples)
        self.assertEqual(0, first_result.updated_samples)
        self.assertEqual(21, self._count_samples("test_importer_"))
        self.assertEqual(sum(len(sample.oracles) for sample in plan.samples), self._count_oracles("test_importer_"))
        self.assertEqual(3, self._count_rows(DatasetSource, "test_importer_"))
        self.assertEqual(3, self._count_rows(AttackDeliveryType, "test_importer_"))
        self.assertEqual(2, self._count_rows(RiskCategory, "test_importer_"))
        self.assertEqual(4, self._count_rows(RiskSubtype, "test_importer_"))
        self.assertEqual(8, self._count_rows(AssetType, "test_importer_"))

        target_sample = next(item for item in plan.samples if item.sample_id == "test_importer_VPI-bench_B2_1_high")
        target_sample.expected_safe_behavior = "updated safe behavior for idempotency test"
        target_sample.oracles[0].display_text = "updated success oracle"

        second_result = apply_import_plan(self.session, plan)
        self.assertEqual(0, second_result.created_samples)
        self.assertEqual(21, second_result.updated_samples)
        self.assertEqual(21, self._count_samples("test_importer_"))
        self.assertEqual(sum(len(sample.oracles) for sample in plan.samples), self._count_oracles("test_importer_"))

        sample_row = self.session.execute(
            select(BenchmarkSample).join(DatasetSource).where(
                DatasetSource.code == "test_importer_vpi_bench",
                BenchmarkSample.sample_id == "test_importer_VPI-bench_B2_1_high",
            )
        ).scalar_one()
        self.assertEqual("updated safe behavior for idempotency test", sample_row.expected_safe_behavior)

        oracle_row = self.session.execute(
            select(SampleOracle)
            .join(BenchmarkSample, BenchmarkSample.id == SampleOracle.sample_id_ref)
            .join(DatasetSource, DatasetSource.id == BenchmarkSample.dataset_source_id)
            .where(
                DatasetSource.code == "test_importer_vpi_bench",
                BenchmarkSample.sample_id == "test_importer_VPI-bench_B2_1_high",
                SampleOracle.oracle_kind == 1,
                SampleOracle.seq_no == 1,
            )
        ).scalar_one()
        self.assertEqual("updated success oracle", oracle_row.display_text)
        self.assertIsNotNone(oracle_row.updated_at)

    def _count_samples(self, prefix: str) -> int:
        return self.session.execute(
            select(func.count())
            .select_from(BenchmarkSample)
            .where(BenchmarkSample.sample_id.like(f"{prefix}%"))
        ).scalar_one()

    def _count_oracles(self, prefix: str) -> int:
        return self.session.execute(
            select(func.count())
            .select_from(SampleOracle)
            .join(BenchmarkSample, BenchmarkSample.id == SampleOracle.sample_id_ref)
            .where(BenchmarkSample.sample_id.like(f"{prefix}%"))
        ).scalar_one()

    def _count_rows(self, model, prefix: str) -> int:
        return self.session.execute(
            select(func.count())
            .select_from(model)
            .where(model.code.like(f"{prefix}%"))
        ).scalar_one()

    def _with_prefix(self, plan, prefix: str):
        prefixed_samples = []
        for sample in plan.samples:
            prefixed_oracles = [replace(oracle) for oracle in sample.oracles]
            prefixed_samples.append(
                replace(
                    sample,
                    sample_id=f"{prefix}_{sample.sample_id}",
                    sample_name=f"{prefix}_{sample.sample_name}",
                    dataset_source_code=f"{prefix}_{sample.dataset_source_code}",
                    dataset_source_name=f"{prefix}_{sample.dataset_source_name}",
                    attack_delivery_type_code=f"{prefix}_{sample.attack_delivery_type_code}",
                    attack_delivery_type_name=f"{prefix}_{sample.attack_delivery_type_name}",
                    risk_category_code=f"{prefix}_{sample.risk_category_code}",
                    risk_category_name=f"{prefix}_{sample.risk_category_name}",
                    risk_subtype_code=f"{prefix}_{sample.risk_subtype_code}",
                    risk_subtype_name=f"{prefix}_{sample.risk_subtype_name}",
                    asset_type_code=f"{prefix}_{sample.asset_type_code}" if sample.asset_type_code else None,
                    asset_type_name=f"{prefix}_{sample.asset_type_name}" if sample.asset_type_name else None,
                    oracles=prefixed_oracles,
                )
            )
        return replace(plan, samples=prefixed_samples)


if __name__ == "__main__":
    unittest.main()
