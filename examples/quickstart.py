"""
DriftMind Client - Complete Quickstart Example

This example demonstrates:
1. Creating a forecaster
2. Feeding data points
3. Getting predictions
4. Inspecting forecaster details
5. Cleaning up resources
"""

import math

from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindApiError, DriftMindError
from driftmind.utils import load_credentials


def main():
    # Load credentials from environment or .env file
    creds = load_credentials()

    # Use context manager for automatic resource cleanup
    with DriftMindClient(
        api_key=creds["DRIFTMIND_API_KEY"], base_url=creds["DRIFTMIND_API_URL"]
    ) as client:
        # 1. Verify API connectivity
        print("Checking API connectivity...")
        try:
            if client.health_check():
                print("✓ Connected to DriftMind API\n")
        except DriftMindApiError as e:
            print(f"✗ API error: {e.message}")
            print(f"   Status: {e.status_code}")
            print(f"   Details: {e.details}")
            # Continue anyway - health check might not be critical
            print("   Continuing anyway...\n")
        except DriftMindError as e:
            print(f"✗ Network error: {e}")
            return

        # 2. Create a forecaster
        print("Creating forecaster...")
        forecaster_payload = {
            "forecaster_name": "Quickstart Demo",
            "features": ["sin", "cos"],
            "input_size": 10,
            "output_size": 3,
        }

        try:
            forecaster_info = client.create_forecaster(forecaster_payload)
            forecaster_id = forecaster_info["forecaster_id"]
            print(f"✓ Created forecaster: {forecaster_id}\n")
        except DriftMindError as e:
            print(f"✗ Failed to create forecaster: {e}")
            return

        # 3. Feed data points (minimum required: input_size + output_size = 13)
        print("Feeding data points...")
        min_points = (
            forecaster_payload["input_size"] + forecaster_payload["output_size"]
        )

        for i in range(min_points + 5):  # Feed a few extra points
            angle = i * 0.1
            data = {"sin": [math.sin(angle)], "cos": [math.cos(angle)]}

            try:
                client.feed_point(forecaster_id, data)
                if (i + 1) % 5 == 0:
                    print(f"  Fed {i + 1} points...")
            except DriftMindError as e:
                print(f"✗ Failed to feed point {i}: {e}")
                return

        print(f"✓ Fed {min_points + 5} points\n")

        # 4. Get predictions
        print("Requesting forecast...")
        try:
            result = client.forecast(forecaster_id)
            print(f"Global Anomaly Score: {result['anomaly_score']:.4f}")

            for feature_name, pred in result["features"].items():
                print(f"\n--- {feature_name} ---")
                print(f"Method: {pred['forecasting_method']}")
                print(f"Predictions: {[f'{v:.4f}' for v in pred['predictions'][:3]]}")
                print(
                    f"Confidence: [{pred['lower_confidence'][0]:.4f}, {pred['upper_confidence'][0]:.4f}]"
                )
        except DriftMindError as e:
            print(f"✗ Failed to get forecast: {e}")
            return

        print()

        # 5. Inspect stored data (optional - may not be available immediately)
        print("Fetching stored data...")
        try:
            history = client.get_forecaster_data(forecaster_id)
            if isinstance(history, dict) and history:
                # Handle potential "data" wrapper from API
                if "data" in history and isinstance(history["data"], dict):
                    history = history["data"]

                print(f"Stored {len(history)} data points")

                # Show first 3 points as sample
                count = 0
                for timestamp, features in history.items():
                    if count >= 3:
                        print("  ...")
                        break
                    # Handle both dict and numeric values
                    if isinstance(features, dict):
                        try:
                            feature_str = ", ".join(
                                f"{k}={v:.4f}"
                                if isinstance(v, (int, float))
                                else f"{k}={v}"
                                for k, v in features.items()
                            )
                            print(f"  {timestamp}: {feature_str}")
                        except Exception:
                            print(f"  {timestamp}: {features}")
                    count += 1
            else:
                print("No data available yet")
        except DriftMindError as e:
            print(f"✗ Failed to get stored data: {e}")
            # Continue anyway - this is not critical

        print()

        # 6. Inspect forecaster details
        print("Fetching forecaster details...")
        try:
            details = client.get_forecaster_details(forecaster_id)
            print(f"Forecaster: {details['forecaster_name']}")
            print(f"Input Size: {details['configuration']['input_size']}")
            print(f"Output Size: {details['configuration']['output_size']}")

            for name, stats in details["features"].items():
                print(f"\nFeature '{name}':")
                print(f"  Active Clusters: {stats['active_clusters']}")
                print(f"  Total Observations: {stats['total_observations']}")
        except DriftMindError as e:
            print(f"✗ Failed to get details: {e}")
            return

        print()

        # 7. Clean up
        print("Cleaning up...")
        try:
            client.delete_forecaster(forecaster_id)
            print(f"✓ Deleted forecaster: {forecaster_id}")
        except DriftMindError as e:
            print(f"✗ Failed to delete forecaster: {e}")


if __name__ == "__main__":
    main()
