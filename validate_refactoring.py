#!/usr/bin/env python3
"""
Validation script for tech_agent endpoint refactoring.

This script demonstrates:
1. Direct endpoint testing without starting server
2. Response validation
3. Comparison of expected vs actual structure
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, "/home/runner/work/gina_tech_test2/gina_tech_test2")

# Mock environment variables to prevent import errors
os.environ["MYAPP_GPT4O_RESOURCE_ENDPOINT"] = "https://mock.openai.azure.com"
os.environ["MYAPP_GPT4O_API_KEY"] = "mock_key"
os.environ["MYAPP_GPT4O_INTENTDETECT"] = "gpt-4"

from fastapi.testclient import TestClient  # noqa: E402

from api_structure.main import app  # noqa: E402

# Test payload from requirements
TEST_PAYLOAD = {
    "cus_id": "GINA_TEST",
    "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
    "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
    "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog",
}


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def validate_response_structure(response_data):
    """Validate the response has the expected structure."""
    checks = []

    # Outer middleware wrapper
    checks.append(("Has 'status' field", "status" in response_data))
    checks.append(("Has 'message' field", "message" in response_data))
    checks.append(("Has 'data' field", "data" in response_data))
    checks.append(("Status is 200", response_data.get("status") == 200))

    # Inner data
    data = response_data.get("data", {})
    checks.append(("Data is not None", data is not None))
    checks.append(("Data has 'status'", "status" in data))
    checks.append(("Data has 'message'", "message" in data))
    checks.append(("Data has 'result'", "result" in data))
    checks.append(("Data status is 200", data.get("status") == 200))

    # Result structure
    result = data.get("result", [])
    checks.append(("Result is list", isinstance(result, list)))
    checks.append(("Result not empty", len(result) > 0))

    if result:
        first = result[0]
        checks.append(("First item has 'renderId'", "renderId" in first))
        checks.append(("First item has 'type'", "type" in first))
        checks.append(("First item has 'message'", "message" in first))
        checks.append(("First item has 'option'", "option" in first))

    return checks


def main():
    """Run validation tests."""
    print_header("Tech Agent Endpoint Validation")

    print("\n📋 Test Configuration:")
    print("  Endpoint: /v1/tech_agent")
    print(f"  Customer ID: {TEST_PAYLOAD['cus_id']}")
    print(f"  Session ID: {TEST_PAYLOAD['session_id'][:20]}...")
    print(f"  User Input: {TEST_PAYLOAD['user_input']}")

    print_header("Testing api_structure Endpoint")

    with TestClient(app) as client:
        # Make request
        print("\n🔄 Sending POST request...")
        response = client.post("/v1/tech_agent", json=TEST_PAYLOAD)

        # Check response
        print(f"📥 Response Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            return 1

        response_data = response.json()

        print_header("Response Structure Validation")

        checks = validate_response_structure(response_data)

        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        print_header("Response Data Preview")

        # Show key parts of response
        print("\n🔍 Outer Wrapper:")
        print(f"  Status: {response_data.get('status')}")
        print(f"  Message: {response_data.get('message')}")

        data = response_data.get("data", {})
        print("\n🔍 Inner Data:")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")

        result = data.get("result", [])
        if result:
            first = result[0]
            print("\n🔍 First Render Item:")
            print(f"  Type: {first.get('type')}")
            print(f"  Message: {first.get('message', '')[:50]}...")
            print(f"  Options: {len(first.get('option', []))} items")

        print_header("Full Response (JSON)")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))

        print_header("Validation Summary")

        if all_passed:
            print("\n✅ All validation checks passed!")
            print("✅ Endpoint is working correctly")
            print("✅ Response structure matches requirements")
            return 0
        else:
            print("\n❌ Some validation checks failed")
            print("⚠️  Please review the output above")
            return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
