"""
Pytest 設定檔
提供共用的 fixtures 和測試配置
"""

import pytest
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """測試環境初始化"""
    print("\n=== 開始整合測試 ===")
    yield
    print("\n=== 測試完成 ===")
