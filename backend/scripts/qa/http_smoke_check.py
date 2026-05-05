"""对已启动后端服务执行一轮真实 HTTP 冒烟校验。"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import delete, select

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.models.benchmark import AttackDeliveryType, BenchmarkSample, DatasetSource, RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta
from app.models.agent import Agent
from app.models.benchmark_run import ExecutionArtifact, ExecutionSummary, OracleResult, RunDataset, RunReport, RunSample, SampleExecution, TestRun
from app.models.user import User
from app.platform.config import settings
from scripts._common import build_sync_engine, build_sync_session_factory


@dataclass
class SmokeContext:
    prefix: str
    dataset_code: str
    user_email: str
    second_user_email: str
    evaluation_id: str | None = None
    avatar_path: Path | None = None


SYNC_ENGINE = build_sync_engine()
SessionLocal = build_sync_session_factory(SYNC_ENGINE)


def parse_args() -> argparse.Namespace:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Run live HTTP smoke checks against a running backend service.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running backend base URL.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP request timeout in seconds.")
    parser.add_argument("--keep-data", action="store_true", help="Keep smoke fixture data for manual inspection.")
    return parser.parse_args()


def session_scope():
    """返回脚本复用的同步 Session。"""
    return SessionLocal()


def ensure(condition: bool, message: str) -> None:
    """把断言失败统一提升为 AssertionError。"""
    if not condition:
        raise AssertionError(message)


def png_bytes() -> bytes:
    """生成最小 PNG 内容，供头像上传接口使用。"""
    image = io.BytesIO()
    image.write(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return image.getvalue()


def seed_dataset(prefix: str) -> str:
    """插入一组最小可用数据集夹具，供接口链路校验复用。"""
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
    """清理烟测写入的数据库记录与上传头像文件。"""
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
        if user_ids:
            session.execute(delete(Agent).where(Agent.user_id.in_(user_ids)))
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
    """校验接口状态码与统一 envelope 结构。"""
    ensure(response.status_code == status_code, f"{response.request.method} {response.request.url.path} expected {status_code}, got {response.status_code}: {response.text}")
    payload = response.json()
    ensure(isinstance(payload, dict), "response must be a JSON object")
    ensure({"code", "data", "message"}.issubset(payload.keys()), "response must use {code, data, message}")
    return payload


def main() -> int:
    """执行匿名访问、用户链路、数据集链路与提交流程的冒烟检查。"""
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
            # 先验证匿名可访问入口以及统一响应结构。
            for path in ["/", "/api/", "/api/v1/"]:
                payload = check_envelope(client.get(path), status_code=200)
                ensure(payload["code"] == 0, f"{path} should return success envelope")

            unauthorized_payload = check_envelope(client.get("/api/v1/user/profile"), status_code=401)
            ensure(unauthorized_payload["code"] == 40100, "unauthorized profile should use 40100")

            # 再串行覆盖认证、资料、数据集、提交与鉴权隔离等关键链路。
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

            templates = check_envelope(client.get("/api/v1/agents/templates"), status_code=200)
            ensure(templates["data"][0]["templateId"] == "http_submit_poll_basic", "agent templates should expose submit-poll template")

            agent_payload = {
                "templateId": "http_submit_poll_basic",
                "name": f"{prefix} agent",
                "description": "http smoke submit",
                "invokeMode": "sync_response",
                "connection": {"baseUrl": "https://agent.example.com", "invokePath": "/run", "requestTimeoutSeconds": 30},
                "auth": {"type": "bearer", "config": {"token": "sk-http-smoke"}},
                "platformInputMapping": {
                    "task": "prompt",
                    "entryUrl": "url",
                    "timeoutSeconds": "timeout_sec",
                    "sampleId": "case_id",
                    "evaluationId": "evaluation_id",
                    "maxSteps": "max_steps",
                },
                "taskRenderMode": "goal_only",
                "customRequestBody": {"engine": "demo"},
                "requestOptions": {},
                "platformOutputMapping": {"status": "status", "finalAnswer": "answer", "errorMessage": "error"},
                "terminalStatuses": ["completed", "failed"],
                "successStatuses": ["completed"],
            }
            create_agent = check_envelope(client.post("/api/v1/agents", headers=headers, json=agent_payload), status_code=200)
            agent_id = create_agent["data"]["agentId"]
            with session_scope() as session:
                agent = session.execute(select(Agent).where(Agent.public_id == agent_id)).scalar_one()
                agent.status = "active"
                session.commit()

            submit_meta = check_envelope(client.get("/api/v1/evaluations/meta"), status_code=200)
            ensure(submit_meta["data"]["submitMethods"] == ["api"], "evaluation meta should expose api submit method")

            submit_payload = {
                "submitMethod": "api",
                "agentId": agent_id,
                "parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "maxSteps": 30},
                "leaderboardDisplayMode": "anonymous",
                "datasetIds": [context.dataset_code],
                "requestId": f"{prefix}_request_001",
            }
            precheck_result = check_envelope(client.post("/api/v1/evaluations/validate", headers=headers, json=submit_payload), status_code=200)
            ensure(precheck_result["data"]["ok"] is True, "evaluation validate should succeed for seeded dataset")
            ensure(precheck_result["data"]["warnings"], "public leaderboard submission should include a warning")

            submit_result = check_envelope(client.post("/api/v1/evaluations", headers=headers, json=submit_payload), status_code=200)
            context.evaluation_id = submit_result["data"]["evaluationId"]
            ensure(submit_result["data"]["status"] == "pending", "submit should create a pending evaluation")

            repeat_submit = check_envelope(client.post("/api/v1/evaluations", headers=headers, json=submit_payload), status_code=200)
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
        # 默认清理烟测数据，避免重复执行时污染本地环境。
        if not args.keep_data:
            cleanup(context)
        SYNC_ENGINE.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
