"""Pydantic models for tech_agent endpoint."""

from typing import Any, Dict, List

from pydantic import BaseModel


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型"""

    cus_id: str
    session_id: str
    chat_id: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str


class KBInfo(BaseModel):
    """Knowledge Base information"""

    kb_no: str
    title: str
    similarity: float
    source: str
    exec_time: float


class OutputData(BaseModel):
    """Output data structure"""

    answer: str
    ask_flag: bool
    hint_candidates: List[Dict[str, Any]]
    kb: Dict[str, Any]


class RenderItem(BaseModel):
    """Render item structure"""

    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any]
    option: List[Any]


class RenderResult(BaseModel):
    """Render result structure"""

    renderTime: int
    render: List[RenderItem]


class TechAgentResponse(BaseModel):
    """技術支援 API 回應模型"""

    status: int
    message: str
    result: List[RenderItem] | List[Dict[str, Any]]


class TechAgentExtractData(BaseModel):
    """Extract data for Cosmos logging"""

    status: int
    type: str
    message: str
    output: OutputData
