"""Pydantic models for tech_agent API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型"""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User input message")
    websitecode: str = Field(..., description="Website code (e.g., 'tw')")
    product_line: str = Field(default="", description="Product line")
    system_code: str = Field(..., description="System code (e.g., 'rog')")


class KbInfo(BaseModel):
    """Knowledge base information."""

    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """技術支援 API 輸出模型"""

    answer: str = Field(default="", description="Answer content")
    ask_flag: bool = Field(default=False, description="Ask flag")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint candidates"
    )
    kb: KbInfo = Field(default_factory=KbInfo, description="KB info")


class RenderItem(BaseModel):
    """Render item for response."""

    renderId: str = Field(..., description="Render ID")
    stream: bool = Field(default=False, description="Stream mode")
    type: str = Field(..., description="Render type")
    message: str = Field(..., description="Message content")
    remark: List[str] = Field(default_factory=list, description="Remarks")
    option: List[Dict[str, Any]] = Field(
        default_factory=list, description="Options"
    )


class TechAgentResult(BaseModel):
    """技術支援 API 結果模型"""

    renderTime: int = Field(..., description="Render timestamp")
    render: List[RenderItem] = Field(..., description="Render items")


class TechAgentResponse(BaseModel):
    """技術支援 API 回應模型"""

    status: int = Field(..., description="Response status code")
    message: str = Field(..., description="Response message")
    result: List[Dict[str, Any]] = Field(
        default_factory=list, description="Result list"
    )
