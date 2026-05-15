from __future__ import annotations

import pytest


@pytest.mark.db
@pytest.mark.integration
def test_evaluation_routes_work_against_real_database(client, api_db_helper) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_owner",
        email=f"{api_db_helper.prefix}_owner@example.com",
    )
    _, other_token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_other",
        email=f"{api_db_helper.prefix}_other@example.com",
    )
    evaluation_id = api_db_helper.seed_evaluation_run(
        user_id=user_id, dataset_code=dataset_code, status="pending"
    )
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/api/v1/evaluations", headers=headers)
    assert list_response.status_code == 200
    assert any(
        item["evaluationId"] == evaluation_id for item in list_response.json()["data"]
    )

    detail_response = client.get(
        f"/api/v1/evaluations/{evaluation_id}", headers=headers
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert detail_payload["evaluationId"] == evaluation_id
    assert detail_payload["status"] == "pending"
    assert detail_payload["datasetIds"] == [dataset_code]

    cancel_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/actions",
        headers=headers,
        json={"action": "cancel"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["status"] == "canceled"

    forbidden_response = client.get(
        f"/api/v1/evaluations/{evaluation_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["code"] == 40300

    missing_response = client.get(
        f"/api/v1/evaluations/{api_db_helper.prefix}_missing", headers=headers
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == 40400

    unauthorized_response = client.get("/api/v1/evaluations")
    assert unauthorized_response.status_code == 401
    assert unauthorized_response.json()["code"] == 40100
