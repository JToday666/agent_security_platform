import unittest

from fastapi.testclient import TestClient

from app.main import app


class HttpContractTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_and_meta_routes_return_envelope(self) -> None:
        for path in ["/", "/api/", "/api/v1/"]:
            response = self.client.get(path)

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("code", payload)
            self.assertIn("message", payload)
            self.assertIn("data", payload)
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["message"], "success")
            self.assertIsInstance(payload["data"], dict)
            self.assertIn("message", payload["data"])

    def test_request_validation_errors_use_envelope_shape(self) -> None:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": "demo-user",
                "email": "invalid-email",
                "password": "secret123",
            },
        )

        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertIn("code", payload)
        self.assertIn("message", payload)
        self.assertIn("data", payload)
        self.assertEqual(payload["code"], 1000)
        self.assertEqual(payload["message"], "请求参数校验失败")
        self.assertIn("errors", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["errors"]), 1)
        self.assertEqual(payload["data"]["errors"][0]["field"], "email")


if __name__ == "__main__":
    unittest.main()
