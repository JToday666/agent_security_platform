import unittest
from unittest.mock import AsyncMock

from app.api.v1.api import api_router
from app.api.v1.endpoints.agents import (
    precheck_submission,
    submit_agent,
    submit_meta,
)
from app.api.v1.endpoints.datasets import get_dataset_catalog, get_dataset_detail
from app.api.v1.endpoints.evaluations import (
    apply_evaluation_action,
    get_evaluation_detail,
    list_evaluations,
)


class ApiRouteRegistrationTestCase(unittest.TestCase):
    def test_v1_router_registers_new_business_routes(self) -> None:
        route_paths = {route.path for route in api_router.routes}

        self.assertIn("/v1/datasets/catalog", route_paths)
        self.assertIn("/v1/datasets/{datasetId}", route_paths)
        self.assertIn("/v1/agents/submit-meta", route_paths)
        self.assertIn("/v1/agents/precheck", route_paths)
        self.assertIn("/v1/agents/submit", route_paths)
        self.assertIn("/v1/evaluations", route_paths)
        self.assertIn("/v1/evaluations/{evaluationId}", route_paths)
        self.assertIn("/v1/evaluations/{evaluationId}/actions", route_paths)


class ApiResponseContractTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_dataset_endpoints_return_wrapped_response(self) -> None:
        service = AsyncMock()
        service.get_catalog.return_value = {"catalogVersion": "2026-04-08T10:00:00Z"}
        service.get_detail.return_value = {"datasetId": "local_file_modification"}

        catalog_response = await get_dataset_catalog(service=service)
        detail_response = await get_dataset_detail(datasetId="local_file_modification", service=service)

        self.assertEqual(catalog_response["code"], 0)
        self.assertEqual(catalog_response["message"], "success")
        self.assertEqual(detail_response["code"], 0)
        self.assertEqual(detail_response["message"], "success")

    async def test_agent_endpoints_return_wrapped_response(self) -> None:
        service = AsyncMock()
        service.get_submit_meta.return_value = {"supportedMethods": ["api", "docker"]}
        service.precheck.return_value = {"ok": True, "warnings": []}
        service.submit.return_value = {
            "evaluationId": "eval_20260408_001",
            "status": "pending",
            "createdAt": "2026-04-08T10:30:00Z",
        }

        meta_response = await submit_meta(service=service)
        precheck_response = await precheck_submission(payload=object(), current_user=object(), service=service)
        submit_response = await submit_agent(
            payload=object(),
            current_user=object(),
            background_tasks=object(),
            service=service,
        )

        self.assertEqual(meta_response["code"], 0)
        self.assertEqual(precheck_response["code"], 0)
        self.assertEqual(submit_response["code"], 0)

    async def test_evaluation_endpoints_return_wrapped_response(self) -> None:
        service = AsyncMock()
        service.list_evaluations.return_value = []
        service.get_evaluation_detail.return_value = {"evaluationId": "eval_20260408_001"}
        service.apply_action.return_value = {"evaluationId": "eval_20260408_001", "status": "paused"}

        list_response = await list_evaluations(current_user=object(), service=service)
        detail_response = await get_evaluation_detail(
            evaluationId="eval_20260408_001",
            current_user=object(),
            service=service,
        )
        action_response = await apply_evaluation_action(
            evaluationId="eval_20260408_001",
            payload=object(),
            current_user=object(),
            background_tasks=object(),
            service=service,
        )

        self.assertEqual(list_response["code"], 0)
        self.assertEqual(detail_response["code"], 0)
        self.assertEqual(action_response["code"], 0)


if __name__ == "__main__":
    unittest.main()
