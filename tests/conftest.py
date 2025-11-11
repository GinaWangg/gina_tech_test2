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

# Add api_structure to path
api_structure_path = project_root / "api_structure"
sys.path.insert(0, str(api_structure_path))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """測試環境初始化"""
    print("\n=== 開始整合測試 ===")
    yield
    print("\n=== 測試完成 ===")


@pytest.fixture(scope="module")
def test_app():
    """Create a minimal test app without client initialization"""
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from api_structure.src.routers.tech_agent_router import tech_agent_endpoint
    from api_structure.src.schemas.tech_agent_schemas import TechAgentInput
    
    # Create minimal app for testing
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=["*"],
        allow_headers=['Content-Type'],
        max_age=3600
    )
    
    @app.post("/v1/tech_agent")
    async def v1_tech_agent(user_input: TechAgentInput, request: Request):
        """技術支援主流程 API"""
        return await tech_agent_endpoint(user_input, request)
    
    return app

