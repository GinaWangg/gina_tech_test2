"""
Pytest 設定檔
提供共用的 fixtures 和測試配置
"""

import pytest
import sys
import os
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Mock environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Mock required environment variables for testing"""
    test_env = {
        "TESTING": "true",
        "TECH_OPENAI_GPT41MINI_PAYGO_EU_AZURE_ENDPOINT": "https://mock.openai.azure.com/",
        "TECH_OPENAI_GPT41MINI_PAYGO_EU_API_KEY": "mock_api_key",
        "TECH_OPENAI_GPT41MINI_PAYGO_EU_API_VERSION": "2024-02-15-preview",
        "TECH_TRANSLATE_CREDENTIALS": "bW9ja19jcmVkZW50aWFscw==",  # base64 encoded mock
        "TECH_COSMOS_URL": "https://mock.cosmos.azure.com",
        "TECH_COSMOS_KEY": "mock_cosmos_key",
        "TECH_COSMOS_DB": "mock_db",
        "TECH_COSMOS_LOOKUP_DB": "mock_lookup_db",
        "TECH_COSMOS_CONTAINER": "mock_container",
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """測試環境初始化"""
    print("\n=== 開始整合測試 ===")
    yield
    print("\n=== 測試完成 ===")
