import unittest

from fastapi.testclient import TestClient

from app.api.v1.api import api_router
from app.main import app


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


class ApiResponseContractTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_unauthorized_profile_request_returns_wrapped_response(self) -> None:
        response = self.client.get("/api/v1/user/profile")

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertEqual(payload["code"], 40100)
        self.assertEqual(payload["message"], "未登录或登录已失效。")
        self.assertIsNone(payload["data"])


if __name__ == "__main__":
    unittest.main()
