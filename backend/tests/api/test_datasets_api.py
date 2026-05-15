from __future__ import annotations

import pytest


@pytest.mark.db
@pytest.mark.integration
def test_dataset_routes_work_against_real_database(client, api_db_helper) -> None:
    dataset_code = api_db_helper.seed_dataset()

    catalog_response = client.get("/api/v1/datasets/catalog")
    assert catalog_response.status_code == 200
    catalog_payload = catalog_response.json()["data"]
    dataset_items = [
        dataset
        for category in catalog_payload["categories"]
        for dataset in category["subcategories"]
        if dataset["datasetId"] == dataset_code
    ]
    assert len(dataset_items) == 1

    detail_response = client.get(f"/api/v1/datasets/{dataset_code}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert detail_payload["datasetId"] == dataset_code
    assert detail_payload["name"] == f"{api_db_helper.prefix} 数据集"
    assert (
        detail_payload["category"]["categoryId"] == f"{api_db_helper.prefix}_category"
    )

    missing_response = client.get(f"/api/v1/datasets/{api_db_helper.prefix}_missing")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == 40400
