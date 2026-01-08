from http import HTTPStatus

import pytest
import responses

from driftmind.exceptions import ForecasterCreationError


@responses.activate
def test_create_forecaster_success(client, base_url):
    # Mocking a successful 201 response
    responses.add(
        responses.POST,
        url=f"{base_url}",
        json={
            "forecaster_id": "fc_001",
            "properties": {
                "input_size": 10,
                "output_size": 1,
                "max_clusters_allowed": 50,
                "similarity_threshold": 0.8,
                "timestamp_interval_in_seconds": 30,
                "fit_rate": 1,
                "use_custom_date_format": True,
                "date_format": "%d-%m-%Y %H:%M",
                "use_initialization_date": True,
                "initialization_date": "01-01-2025 00:00",
            },
        },
        headers={"Location": f"{base_url}/forecaster/fc_001"},
        status=HTTPStatus.CREATED,
    )

    payload = {
        "forecaster_name": "Test",
        "features": ["f1", "f2"],
        "input_size": 10,
        "output_size": 1,
    }

    result = client.create_forecaster(payload)
    assert result["forecaster_id"] == "fc_001"


@responses.activate(assert_all_requests_are_fired=True)
def test_create_forecaster_api_error(client, base_url):
    # Mocking a 400 error
    responses.add(
        responses.POST,
        url=f"{base_url}",
        json=["Invalid input size"],
        status=HTTPStatus.BAD_REQUEST,
    )

    with pytest.raises(ForecasterCreationError) as exc:
        client.create_forecaster(
            {
                "forecaster_name": "Test",
                "features": ["f1"],
                "input_size": 10,
                "output_size": 1,
            }
        )

    assert "Bad Request: Invalid input size" in str(exc.value)
