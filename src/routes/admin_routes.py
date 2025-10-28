# src/api/admin_routes.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.services.update_service import UpdateService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/update_technical_rag")
async def update_technical_rag_endpoint(request: Request):
    """
    更新技術 RAG 資料
    從資料庫重新載入 sample_question 並更新 mappings
    """
    containers = request.app.state.container
    update_service = UpdateService(containers)
    result = await update_service.update_technical_rag()
    return JSONResponse(content=result)


@router.get("/update_botname")
def update_website_botname_endpoint(request: Request):
    """
    更新網站機器人名稱對應
    從資料庫重新載入 websitecode 和 productline 的對應關係
    """
    containers = request.app.state.container
    update_service = UpdateService(containers)
    result = update_service.update_website_botname()
    return JSONResponse(content=result)


@router.get("/update_KB")
def update_KB_endpoint(request: Request):
    """
    更新知識庫資料
    從資料庫重新載入 ApChatbotKnowledge
    """
    containers = request.app.state.container
    update_service = UpdateService(containers)
    result = update_service.update_KB()
    return JSONResponse(content=result)


@router.get("/update_specific_KB")
def update_specific_KB_endpoint(request: Request):
    """
    更新特定知識庫對應
    從資料庫重新載入 specific_kb_bot_scope
    """
    containers = request.app.state.container
    update_service = UpdateService(containers)
    result = update_service.update_specific_KB()
    return JSONResponse(content=result)
