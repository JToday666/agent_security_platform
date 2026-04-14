from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.benchmark import AttackDeliveryType, BenchmarkSample, DatasetSource, RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta
from app.models.benchmark_run import ExecutionArtifact, ExecutionSummary, OracleResult, RunDataset, RunReport, RunSample, SampleExecution, TestRun
from app.models.user import User
from app.shared.config import settings


@dataclass
class SmokeContext:
    prefix: str
    dataset_code: str
    user_email: str
    second_user_email: str
    evaluation_id: str | None = None
    avatar_path: Path | None = None


SYNC_ENGINE = create_engine(settings.SYNC_DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=SYNC_ENGINE, future=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live HTTP smoke checks against a running backend service.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running backend base URL.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP request timeout in seconds.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke fixture data for manual inspection.")
    return parser.parse_args()


def session_scope() -> Session:
    return SessionLocal()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def png_bytes() -> bytes:
    image = io.BytesIO()
    image.write(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return image.getvalue()


def seed_dataset(prefix: str) -> str:
    dataset_code = f"{prefix}_dataset"
    with session_scope() as session:
        category = RiskCategory(
            code=f"{prefix}_category",
            name=f"{prefix} 大类",
            meaning="HTTP 烟测大类",
            description="真实 HTTP 冒烟数据",
            sort_order=1,
            is_active=True,
        )
        source = DatasetSource(code=f"{prefix}_source", name=f"{prefix} source", is_active=True)
        delivery = AttackDeliveryType(code=f"{prefix}_delivery", name=f"{prefix} delivery", is_active=True)
        session.add_all([category, source, delivery])
        session.flush()

        subtype = RiskSubtype(
            category_id=category.id,
            code=dataset_code,
            name=f"{prefix} 数据集",
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
                sample_id=f"{prefix}_sample",
                sample_name=f"{prefix} sample",
                resource_path=f"{prefix}/resource",
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


def cleanup(context: SmokeContext) -> None:
    with session_scope() as session:
        user_ids = list(
            (
                session.execute(
                    select(User.id).where(
                        User.email.in_([context.user_email, context.second_user_email])
                    )
                )
            ).scalars()
        )
        run_ids = list(
            (
                session.execute(
                    select(TestRun.id).where(
                        (TestRun.public_id.like(f"eval_{context.prefix}%")) | (TestRun.user_id.in_(user_ids) if user_ids else False)
                    )
                )
            ).scalars()
        )
        subtype_ids = list(
            (
                session.execute(select(RiskSubtype.id).where(RiskSubtype.code.like(f"{context.prefix}%")))
            ).scalars()
        )
        sample_ids: list[int] = []
        sample_execution_ids: list[int] = []

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
        session.execute(delete(RiskCategory).where(RiskCategory.code.like(f"{context.prefix}%")))
        session.execute(delete(DatasetSource).where(DatasetSource.code.like(f"{context.prefix}%")))
        session.execute(delete(AttackDeliveryType).where(AttackDeliveryType.code.like(f"{context.prefix}%")))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()

    if context.avatar_path and context.avatar_path.exists():
        context.avatar_path.unlink()


def check_envelope(response: httpx.Response, *, status_code: int) -> dict:
    ensure(response.status_code == status_code, f"{response.request.method} {response.request.url.path} expected {status_code}, got {response.status_code}: {response.text}")
    payload = response.json()
    ensure(isinstance(payload, dict), "response must be a JSON object")
    ensure({"code", "data", "message"}.issubset(payload.keys()), "response must use {code, data, message}")
    return payload


def main() -> int:
    args = parse_args()
    prefix = f"http_smoke_{uuid4().hex[:8]}"
    context = SmokeContext(
        prefix=prefix,
        dataset_code=seed_dataset(prefix),
        user_email=f"{prefix}@example.com",
        second_user_email=f"{prefix}_other@example.com",
    )

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
            for path in ["/", "/api/", "/api/v1/"]:
                payload = check_envelope(client.get(path), status_code=200)
                ensure(payload["code"] == 0, f"{path} should return success envelope")

            unauthorized_payload = check_envelope(client.get("/api/v1/user/profile"), status_code=401)
            ensure(unauthorized_payload["code"] == 40100, "unauthorized profile should use 40100")

            register_payload = {
                "username": f"{prefix}_user",
                "email": context.user_email,
                "password": "secret123",
            }
            register_result = check_envelope(client.post("/api/v1/auth/register", json=register_payload), status_code=200)
            token = register_result["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            login_result = check_envelope(
                client.post(
                    "/api/v1/auth/login",
                    json={"username": register_payload["username"], "password": register_payload["password"]},
                ),
                status_code=200,
            )
            ensure(login_result["data"]["user"]["email"] == context.user_email, "login response should include registered user")

            me_result = check_envelope(client.get("/api/v1/auth/me", headers=headers), status_code=200)
            ensure(me_result["data"]["username"] == register_payload["username"], "me endpoint should return current user")

            profile_result = check_envelope(client.get("/api/v1/user/profile", headers=headers), status_code=200)
            ensure(profile_result["data"]["email"] == context.user_email, "profile endpoint should return current user email")

            renamed_username = f"{prefix}_renamed"
            update_result = check_envelope(
                client.put("/api/v1/user/profile", headers=headers, json={"username": renamed_username}),
                status_code=200,
            )
            ensure(update_result["data"]["username"] == renamed_username, "profile update should return renamed username")

            avatar_result = check_envelope(
                client.post(
                    "/api/v1/user/avatar",
                    headers=headers,
                    files={"avatar": ("avatar.png", png_bytes(), "image/png")},
                ),
                status_code=200,
            )
            avatar_url = avatar_result["data"]["avatarUrl"]
            context.avatar_path = settings.avatars_root / avatar_url.rsplit("/", 1)[-1]
            ensure(context.avatar_path.exists(), "uploaded avatar file should exist on disk")

            catalog_result = check_envelope(client.get("/api/v1/datasets/catalog"), status_code=200)
            dataset_items = [
                dataset
                for category in catalog_result["data"]["categories"]
                for dataset in category["subcategories"]
                if dataset["datasetId"] == context.dataset_code
            ]
            ensure(len(dataset_items) == 1, "catalog should include seeded dataset")

            detail_result = check_envelope(client.get(f"/api/v1/datasets/{context.dataset_code}"), status_code=200)
            ensure(detail_result["data"]["datasetId"] == context.dataset_code, "dataset detail should return seeded dataset")

            missing_dataset = check_envelope(client.get(f"/api/v1/datasets/{prefix}_missing"), status_code=404)
            ensure(missing_dataset["code"] == 40400, "missing dataset should use 40400")

            submit_meta = check_envelope(client.get("/api/v1/agents/submit-meta"), status_code=200)
            ensure(submit_meta["data"]["supportedMethods"] == ["api", "docker"], "submit-meta should expose supported methods")

            submit_payload = {
                "agentName": f"{prefix} agent",
                "description": "http smoke submit",
                "submitMethod": "api",
                "api": {"baseUrl": "https://example.com/agent", "token": "sk-http-smoke"},
                "parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False},
                "publicToLeaderboard": False,
                "datasetIds": [context.dataset_code],
                "requestId": f"{prefix}_request_001",
            }
            precheck_result = check_envelope(client.post("/api/v1/agents/precheck", headers=headers, json=submit_payload), status_code=200)
            ensure(precheck_result["data"] == {"ok": True, "warnings": []}, "precheck should succeed for seeded dataset")

            submit_result = check_envelope(client.post("/api/v1/agents/submit", headers=headers, json=submit_payload), status_code=200)
            context.evaluation_id = submit_result["data"]["evaluationId"]
            ensure(submit_result["data"]["status"] == "pending", "submit should create a pending evaluation")

            repeat_submit = check_envelope(client.post("/api/v1/agents/submit", headers=headers, json=submit_payload), status_code=200)
            ensure(repeat_submit["data"]["evaluationId"] == context.evaluation_id, "repeated submit should reuse the same evaluation")

            evaluation_list = check_envelope(client.get("/api/v1/evaluations", headers=headers), status_code=200)
            ensure(
                any(item["evaluationId"] == context.evaluation_id for item in evaluation_list["data"]),
                "evaluation list should include submitted run",
            )

            evaluation_detail = check_envelope(client.get(f"/api/v1/evaluations/{context.evaluation_id}", headers=headers), status_code=200)
            ensure(evaluation_detail["data"]["status"] == "pending", "new evaluation should start in pending status")

            cancel_result = check_envelope(
                client.post(f"/api/v1/evaluations/{context.evaluation_id}/actions", headers=headers, json={"action": "cancel"}),
                status_code=200,
            )
            ensure(cancel_result["data"]["status"] == "canceled", "cancel action should finish pending run immediately")

            other_register = check_envelope(
                client.post(
                    "/api/v1/auth/register",
                    json={"username": f"{prefix}_other", "email": context.second_user_email, "password": "secret123"},
                ),
                status_code=200,
            )
            other_headers = {"Authorization": f"Bearer {other_register['data']['token']}"}
            forbidden_result = check_envelope(
                client.get(f"/api/v1/evaluations/{context.evaluation_id}", headers=other_headers),
                status_code=403,
            )
            ensure(forbidden_result["code"] == 40300, "other user should not access evaluation detail")

        print(f"HTTP smoke check passed for {args.base_url.rstrip('/')} with prefix {prefix}")
        return 0
    except httpx.HTTPError as exc:
        print(f"HTTP smoke check failed: cannot reach {args.base_url.rstrip('/')} - {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"HTTP smoke check failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if not args.keep_data:
            cleanup(context)
        SYNC_ENGINE.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
