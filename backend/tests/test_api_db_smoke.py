from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.benchmark import AttackDeliveryType, BenchmarkSample, DatasetSource, RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta
from app.models.benchmark_run import ExecutionArtifact, ExecutionSummary, OracleResult, RunDataset, RunReport, RunSample, SampleExecution, TestRun
from app.models.user import User
from app.shared.config import settings
from app.shared.security import create_access_token, hash_password


class ApiDatabaseSmokeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync_engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
        cls.SessionLocal = sessionmaker(bind=cls.sync_engine, future=True)
        cls.client_ctx = TestClient(app)
        cls.client = cls.client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_ctx.__exit__(None, None, None)
        cls.sync_engine.dispose()

    def setUp(self) -> None:
        self.prefix = f"smoke_{uuid4().hex[:8]}"
        self.created_avatar_paths: list[Path] = []

    def tearDown(self) -> None:
        for path in self.created_avatar_paths:
            if path.exists():
                path.unlink()
        self._cleanup_db()

    def test_auth_and_user_routes_work_against_real_database(self) -> None:
        register_payload = {
            "username": f"{self.prefix}_alice",
            "email": f"{self.prefix}@example.com",
            "password": "secret123",
        }

        register_response = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(register_response.status_code, 200)
        register_data = register_response.json()["data"]
        token = register_data["token"]

        login_response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": register_payload["username"],
                "password": register_payload["password"],
            },
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["data"]["user"]["email"], register_payload["email"])

        headers = {"Authorization": f"Bearer {token}"}
        me_response = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["data"]["username"], register_payload["username"])

        profile_response = self.client.get("/api/v1/user/profile", headers=headers)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["data"]["email"], register_payload["email"])

        update_response = self.client.put(
            "/api/v1/user/profile",
            headers=headers,
            json={"username": f"{self.prefix}_renamed"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["data"]["username"], f"{self.prefix}_renamed")

        with TemporaryDirectory() as tmpdir:
            avatars_root = Path(tmpdir)
            with patch.object(type(settings), "avatars_root", new_callable=PropertyMock, return_value=avatars_root):
                avatar_response = self.client.post(
                    "/api/v1/user/avatar",
                    headers=headers,
                    files={"avatar": ("avatar.png", self._png_bytes(), "image/png")},
                )
            self.assertEqual(avatar_response.status_code, 200)
            avatar_url = avatar_response.json()["data"]["avatarUrl"]
            self.assertTrue(avatar_url.startswith("/uploads/avatars/"))
            avatar_path = avatars_root / avatar_url.rsplit("/", 1)[-1]
            self.assertTrue(avatar_path.exists())

        unauthorized_response = self.client.get("/api/v1/user/profile")
        self.assertEqual(unauthorized_response.status_code, 401)
        self.assertEqual(unauthorized_response.json()["code"], 40100)

    def test_dataset_routes_work_against_real_database(self) -> None:
        dataset_code = self._seed_dataset()

        catalog_response = self.client.get("/api/v1/datasets/catalog")
        self.assertEqual(catalog_response.status_code, 200)
        catalog_payload = catalog_response.json()["data"]
        dataset_items = [
            dataset
            for category in catalog_payload["categories"]
            for dataset in category["subcategories"]
            if dataset["datasetId"] == dataset_code
        ]
        self.assertEqual(len(dataset_items), 1)

        detail_response = self.client.get(f"/api/v1/datasets/{dataset_code}")
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()["data"]
        self.assertEqual(detail_payload["datasetId"], dataset_code)
        self.assertEqual(detail_payload["name"], f"{self.prefix} 数据集")
        self.assertEqual(detail_payload["category"]["categoryId"], f"{self.prefix}_category")

        missing_response = self.client.get(f"/api/v1/datasets/{self.prefix}_missing")
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(missing_response.json()["code"], 40400)

    def test_submission_routes_work_against_real_database(self) -> None:
        dataset_code = self._seed_dataset()
        user_id, token = self._seed_user(username=f"{self.prefix}_submitter", email=f"{self.prefix}_submit@example.com")
        self.assertGreater(user_id, 0)
        headers = {"Authorization": f"Bearer {token}"}

        submit_meta_response = self.client.get("/api/v1/agents/submit-meta")
        self.assertEqual(submit_meta_response.status_code, 200)
        meta_payload = submit_meta_response.json()["data"]
        self.assertEqual(meta_payload["supportedMethods"], ["api", "docker"])

        payload = {
            "agentName": f"{self.prefix} agent",
            "description": "db smoke submit",
            "submitMethod": "api",
            "api": {
                "baseUrl": "https://example.com/agent",
                "token": "sk-smoke",
            },
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "retryEnabled": False,
            },
            "publicToLeaderboard": False,
            "datasetIds": [dataset_code],
            "requestId": f"{self.prefix}_request_001",
        }

        precheck_response = self.client.post("/api/v1/agents/precheck", headers=headers, json=payload)
        self.assertEqual(precheck_response.status_code, 200)
        self.assertEqual(precheck_response.json()["data"], {"ok": True, "warnings": []})

        submit_response = self.client.post("/api/v1/agents/submit", headers=headers, json=payload)
        self.assertEqual(submit_response.status_code, 200)
        first_submit = submit_response.json()["data"]
        self.assertEqual(first_submit["status"], "pending")

        repeat_submit_response = self.client.post("/api/v1/agents/submit", headers=headers, json=payload)
        self.assertEqual(repeat_submit_response.status_code, 200)
        repeat_submit = repeat_submit_response.json()["data"]
        self.assertEqual(repeat_submit["evaluationId"], first_submit["evaluationId"])
        self.assertEqual(repeat_submit["status"], first_submit["status"])

    def test_evaluation_routes_work_against_real_database(self) -> None:
        dataset_code = self._seed_dataset()
        user_id, token = self._seed_user(username=f"{self.prefix}_owner", email=f"{self.prefix}_owner@example.com")
        _, other_token = self._seed_user(username=f"{self.prefix}_other", email=f"{self.prefix}_other@example.com")
        evaluation_id = self._seed_evaluation_run(user_id=user_id, dataset_code=dataset_code, status="pending")
        headers = {"Authorization": f"Bearer {token}"}

        list_response = self.client.get("/api/v1/evaluations", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()["data"]
        self.assertTrue(any(item["evaluationId"] == evaluation_id for item in list_payload))

        detail_response = self.client.get(f"/api/v1/evaluations/{evaluation_id}", headers=headers)
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()["data"]
        self.assertEqual(detail_payload["evaluationId"], evaluation_id)
        self.assertEqual(detail_payload["status"], "pending")
        self.assertEqual(detail_payload["datasetIds"], [dataset_code])

        cancel_response = self.client.post(
            f"/api/v1/evaluations/{evaluation_id}/actions",
            headers=headers,
            json={"action": "cancel"},
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.json()["data"]["status"], "canceled")

        forbidden_response = self.client.get(
            f"/api/v1/evaluations/{evaluation_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        self.assertEqual(forbidden_response.status_code, 403)
        self.assertEqual(forbidden_response.json()["code"], 40300)

        missing_response = self.client.get(f"/api/v1/evaluations/{self.prefix}_missing", headers=headers)
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(missing_response.json()["code"], 40400)

        unauthorized_response = self.client.get("/api/v1/evaluations")
        self.assertEqual(unauthorized_response.status_code, 401)
        self.assertEqual(unauthorized_response.json()["code"], 40100)

    def _session(self) -> Session:
        return self.SessionLocal()

    def _seed_user(self, username: str, email: str) -> tuple[int, str]:
        with self._session() as session:
            user = User(username=username, email=email, hashed_password=hash_password("secret123"))
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id, create_access_token(user.id)

    def _seed_dataset(self) -> str:
        dataset_code = f"{self.prefix}_dataset"
        with self._session() as session:
            category = RiskCategory(
                code=f"{self.prefix}_category",
                name=f"{self.prefix} 大类",
                meaning="烟测大类",
                description="真实数据库烟测数据",
                sort_order=1,
                is_active=True,
            )
            source = DatasetSource(code=f"{self.prefix}_source", name=f"{self.prefix} source", is_active=True)
            delivery = AttackDeliveryType(code=f"{self.prefix}_delivery", name=f"{self.prefix} delivery", is_active=True)
            session.add_all([category, source, delivery])
            session.flush()

            subtype = RiskSubtype(
                category_id=category.id,
                code=dataset_code,
                name=f"{self.prefix} 数据集",
                sort_order=1,
                is_active=True,
            )
            session.add(subtype)
            session.flush()

            session.add(
                RiskSubtypeDisplayMeta(
                    subtype_id=subtype.id,
                    short_description="短描述",
                    full_description="完整描述",
                    highlights=["亮点一"],
                    scenarios=["场景一"],
                    resources=[{"label": "文档", "url": "https://example.com/docs", "type": "docs"}],
                    media=[{"mediaId": "demo", "type": "image", "title": "示意图", "description": "desc", "url": "https://example.com/image.png", "coverUrl": None, "sort": 1}],
                )
            )
            session.add(
                BenchmarkSample(
                    dataset_source_id=source.id,
                    sample_id=f"{self.prefix}_sample",
                    sample_name=f"{self.prefix} sample",
                    resource_path=f"{self.prefix}/resource",
                    entry_path="index.html",
                    user_goal="完成正常任务",
                    attacker_goal="诱导攻击",
                    attacker_is_user=False,
                    attack_delivery_type_id=delivery.id,
                    risk_subtype_id=subtype.id,
                    risk_level=2,
                    attack_level=2,
                    difficulty_seed=Decimal("0.500"),
                    difficulty_score=Decimal("0.500"),
                    asset_type_id=None,
                    expected_safe_behavior="拒绝攻击并完成正常任务",
                    is_active=True,
                )
            )
            session.commit()
        return dataset_code

    def _seed_evaluation_run(self, user_id: int, dataset_code: str, status: str) -> str:
        with self._session() as session:
            subtype_row = session.execute(select(RiskSubtype.id, RiskSubtype.name).where(RiskSubtype.code == dataset_code)).one()
            dataset_name = subtype_row.name
            public_id = f"eval_{self.prefix}"
            now = datetime.now(timezone.utc)
            run = TestRun(
                user_id=user_id,
                public_id=public_id,
                agent_name=f"{self.prefix} agent",
                description="评测烟测任务",
                submit_method="api",
                public_to_leaderboard=False,
                request_id=f"{self.prefix}_eval_request",
                agent_base_url="https://example.com/agent",
                credential_ref=None,
                status=status,
                sample_query_snapshot={"datasetIds": [dataset_code]},
                execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
                total_samples=1,
                completed_samples=0,
                success_count=0,
                failed_count=0,
                created_at=now,
                updated_at=now,
            )
            session.add(run)
            session.flush()
            session.add(
                RunDataset(
                    run_id=run.id,
                    dataset_code=dataset_code,
                    dataset_name=dataset_name,
                    order_no=1,
                    status=status,
                    total_samples=1,
                    completed_samples=0,
                )
            )
            session.commit()
        return public_id

    def _cleanup_db(self) -> None:
        with self._session() as session:
            user_ids = list(
                (
                    session.execute(select(User.id).where(User.email.like(f"{self.prefix}%@example.com")))
                ).scalars()
            )
            run_ids = list(
                (
                    session.execute(
                        select(TestRun.id).where(
                            (TestRun.public_id.like(f"eval_{self.prefix}%")) | (TestRun.user_id.in_(user_ids) if user_ids else False)
                        )
                    )
                ).scalars()
            )
            sample_execution_ids = []
            sample_ids = []
            subtype_ids = list(
                (
                    session.execute(select(RiskSubtype.id).where(RiskSubtype.code.like(f"{self.prefix}%")))
                ).scalars()
            )
            if run_ids:
                sample_execution_ids = list(
                    (
                        session.execute(select(SampleExecution.id).where(SampleExecution.run_id.in_(run_ids)))
                    ).scalars()
                )
                session.execute(delete(RunReport).where(RunReport.run_id.in_(run_ids)))
            if sample_execution_ids:
                session.execute(delete(ExecutionArtifact).where(ExecutionArtifact.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(OracleResult).where(OracleResult.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(ExecutionSummary).where(ExecutionSummary.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(SampleExecution).where(SampleExecution.id.in_(sample_execution_ids)))
            if run_ids:
                session.execute(delete(RunSample).where(RunSample.run_id.in_(run_ids)))
                session.execute(delete(RunDataset).where(RunDataset.run_id.in_(run_ids)))
                session.execute(delete(TestRun).where(TestRun.id.in_(run_ids)))
            if subtype_ids:
                sample_ids = list(
                    (
                        session.execute(select(BenchmarkSample.id).where(BenchmarkSample.risk_subtype_id.in_(subtype_ids)))
                    ).scalars()
                )
            if sample_ids:
                session.execute(delete(BenchmarkSample).where(BenchmarkSample.id.in_(sample_ids)))
            if subtype_ids:
                session.execute(delete(RiskSubtypeDisplayMeta).where(RiskSubtypeDisplayMeta.subtype_id.in_(subtype_ids)))
                session.execute(delete(RiskSubtype).where(RiskSubtype.id.in_(subtype_ids)))
            session.execute(delete(RiskCategory).where(RiskCategory.code.like(f"{self.prefix}%")))
            session.execute(delete(DatasetSource).where(DatasetSource.code.like(f"{self.prefix}%")))
            session.execute(delete(AttackDeliveryType).where(AttackDeliveryType.code.like(f"{self.prefix}%")))
            if user_ids:
                session.execute(delete(User).where(User.id.in_(user_ids)))
            session.commit()

    @staticmethod
    def _png_bytes() -> bytes:
        image = io.BytesIO()
        image.write(
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return image.getvalue()


if __name__ == "__main__":
    unittest.main()
