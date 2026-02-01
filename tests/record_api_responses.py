"""
Record real API responses for comprehensive test fixtures.

Run this script to capture actual API responses for both success and error cases.
"""

import json
from pathlib import Path

from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindApiError
from driftmind.utils import load_credentials

REQUESTS_DIR = Path("tests/fixtures/requests")
RESPONSES_SUCCESS_DIR = Path("tests/fixtures/responses/success")
RESPONSES_ERRORS_DIR = Path("tests/fixtures/responses/errors")


def save_json(path: Path, data: dict):
    """Save data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved: {path}")


def record_interaction(
    endpoint: str,
    scenario: str,
    request_payload: dict | None,
    response_data: dict,
    status_code: int,
):
    """Record both request and response."""
    # Save request if provided
    if request_payload:
        req_path = REQUESTS_DIR / f"{endpoint}_{scenario}.json"
        save_json(req_path, request_payload)

    # Save response
    if 200 <= status_code < 300:
        resp_path = RESPONSES_SUCCESS_DIR / f"{endpoint}_{status_code}.json"
    else:
        resp_path = RESPONSES_ERRORS_DIR / f"{endpoint}_{status_code}_{scenario}.json"

    save_json(resp_path, {"status_code": status_code, "body": response_data})


def main():
    print("Loading credentials...")
    creds = load_credentials()
    client = DriftMindClient(creds["DRIFTMIND_API_KEY"], creds["DRIFTMIND_API_URL"])

    print("\n=== Recording Success Cases ===\n")

    # 1. Create forecaster - minimal
    print("1. Create forecaster (minimal)...")
    payload = {
        "forecaster_name": "RecorderTest_Minimal",
        "features": ["sin", "cos"],
        "input_size": 10,
        "output_size": 3,
    }
    try:
        response = client.create_forecaster(payload)
        record_interaction("create_forecaster", "minimal", payload, response, 201)
        forecaster_id = response["forecaster_id"]
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # 2. Get forecaster details
    print("2. Get forecaster details...")
    try:
        response = client.get_forecaster_details(forecaster_id)
        record_interaction("get_forecaster_details", "success", None, response, 200)
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 3. Feed data - single point
    print("3. Feed data (single point)...")
    feed_payload = {"sin": [0.5], "cos": [0.8]}
    try:
        response = client.feed_point(forecaster_id, feed_payload)
        record_interaction("feed_data", "single_point", feed_payload, response, 200)
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 4. Feed more data to reach minimum
    print("4. Feeding more data...")
    for i in range(12):
        try:
            client.feed_point(forecaster_id, {"sin": [0.1 * i], "cos": [0.9 - 0.1 * i]})
        except Exception:
            pass

    # 5. Forecast
    print("5. Get forecast...")
    try:
        response = client.forecast(forecaster_id)
        record_interaction("forecast", "success", None, response, 200)
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 6. Get forecaster data
    print("6. Get forecaster data...")
    try:
        response = client.get_forecaster_data(forecaster_id)
        record_interaction("get_forecaster_data", "success", None, response, 200)
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 7. List forecasters
    print("7. List forecasters...")
    try:
        response = client.list_forecasters()
        record_interaction("list_forecasters", "success", None, response, 200)
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n=== Recording Error Cases ===\n")

    # 8. Duplicate forecaster name (409)
    print("8. Create forecaster with duplicate name...")
    try:
        client.create_forecaster(payload)  # Same name as before
    except DriftMindApiError as e:
        record_interaction(
            "create_forecaster",
            "duplicate_name",
            payload,
            {"error": e.error_code, "details": e.details},
            e.status_code,
        )
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # 9. Feed data with wrong features (400)
    print("9. Feed data with wrong features...")
    wrong_payload = {"wrong_feature": [0.5], "another_wrong": [0.8]}
    try:
        client.feed_point(forecaster_id, wrong_payload)
    except DriftMindApiError as e:
        record_interaction(
            "feed_data",
            "wrong_features",
            wrong_payload,
            {"error": e.error_code, "details": e.details},
            e.status_code,
        )
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # 10. Get details for nonexistent forecaster (404)
    print("10. Get details for nonexistent forecaster...")
    try:
        client.get_forecaster_details("nonexistent-id-12345")
    except DriftMindApiError as e:
        record_interaction(
            "get_forecaster_details",
            "not_found",
            None,
            {"error": e.error_code, "details": e.details},
            e.status_code,
        )
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # 11. Forecast with insufficient data
    print("11. Forecast with insufficient data...")
    new_forecaster = client.create_forecaster(
        {
            "forecaster_name": "RecorderTest_NoData",
            "features": ["x"],
            "input_size": 10,
            "output_size": 3,
        }
    )
    try:
        client.forecast(new_forecaster["forecaster_id"])
    except DriftMindApiError as e:
        record_interaction(
            "forecast",
            "insufficient_data",
            None,
            {"error": e.error_code, "details": e.details},
            e.status_code,
        )
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Cleanup
    print("\n=== Cleanup ===\n")
    try:
        client.delete_forecaster(forecaster_id)
        print(f"✓ Deleted forecaster: {forecaster_id}")
    except Exception as e:
        print(f"✗ Failed to delete: {e}")

    try:
        client.delete_forecaster(new_forecaster["forecaster_id"])
        print(f"✓ Deleted forecaster: {new_forecaster['forecaster_id']}")
    except Exception as e:
        print(f"✗ Failed to delete: {e}")

    print("\n=== Recording Bulk Operations ===\n")

    # Create forecaster for bulk operations
    bulk_forecaster = client.create_forecaster(
        {
            "forecaster_name": "RecorderTest_Bulk",
            "features": ["sin", "cos"],
            "input_size": 10,
            "output_size": 3,
        }
    )
    bulk_forecaster_id = bulk_forecaster["forecaster_id"]

    # 12. Bulk feed data - single forecaster
    print("12. Bulk feed data (single forecaster)...")
    bulk_payload_single = {
        "payloads_list": [
            {
                "forecaster_id": bulk_forecaster_id,
                "data": {"sin": [0.1, 0.2, 0.3], "cos": [0.9, 0.8, 0.7]},
            }
        ]
    }
    try:
        response = client.bulk_feed_data(bulk_payload_single)
        record_interaction(
            "bulk_feed_data", "single", bulk_payload_single, response, 200
        )
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 13. Bulk feed data - multiple forecasters (partial success - 206)
    print("13. Bulk feed data (partial success - one invalid forecaster)...")
    bulk_payload_partial = {
        "payloads_list": [
            {
                "forecaster_id": bulk_forecaster_id,
                "data": {"sin": [0.4, 0.5], "cos": [0.6, 0.5]},
            },
            {
                "forecaster_id": "nonexistent-forecaster-id",
                "data": {"sin": [1.0, 2.0], "cos": [3.0, 4.0]},
            },
        ]
    }
    try:
        response = client.bulk_feed_data(bulk_payload_partial)
        status = 200
        if "results" in response:
            statuses = [r["status"] for r in response["results"]]
            if all(s == 200 for s in statuses):
                status = 200
            elif any(s == 200 for s in statuses):
                status = 206
            else:
                status = 417
        record_interaction(
            "bulk_feed_data", "partial", bulk_payload_partial, response, status
        )
    except Exception as e:
        print(f"✗ Failed: {e}")

    # 14. Bulk feed data - multiple valid forecasters (all success - 200)
    print("14. Bulk feed data (multiple valid forecasters)...")
    forecaster2 = client.create_forecaster(
        {
            "forecaster_name": "RecorderTest_Bulk2",
            "features": ["x", "y"],
            "input_size": 5,
            "output_size": 1,
        }
    )
    forecaster2_id = forecaster2["forecaster_id"]

    bulk_payload_multiple = {
        "payloads_list": [
            {
                "forecaster_id": bulk_forecaster_id,
                "data": {"sin": [0.4, 0.5], "cos": [0.6, 0.5]},
            },
            {
                "forecaster_id": forecaster2_id,
                "data": {"x": [1.0, 2.0], "y": [3.0, 4.0]},
            },
        ]
    }
    try:
        response = client.bulk_feed_data(bulk_payload_multiple)
        status = 200
        if "results" in response:
            statuses = [r["status"] for r in response["results"]]
            if all(s == 200 for s in statuses):
                status = 200
            elif any(s == 200 for s in statuses):
                status = 206
            else:
                status = 417
        record_interaction(
            "bulk_feed_data", "multiple", bulk_payload_multiple, response, status
        )
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Cleanup bulk forecasters
    try:
        client.delete_forecaster(bulk_forecaster_id)
        print(f"✓ Deleted forecaster: {bulk_forecaster_id}")
    except Exception as e:
        print(f"✗ Failed to delete: {e}")

    try:
        client.delete_forecaster(forecaster2_id)
        print(f"✓ Deleted forecaster: {forecaster2_id}")
    except Exception as e:
        print(f"✗ Failed to delete: {e}")

    client.close()
    print("\n✅ Recording complete!")


if __name__ == "__main__":
    main()
