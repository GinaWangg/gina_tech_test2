"""Pydantic models for tech agent API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """Tech agent API input model."""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User input message")
    websitecode: str = Field(..., description="Website code (e.g., tw, us)")
    product_line: str = Field(
        default="", description="Product line (optional)"
    )
    system_code: str = Field(..., description="System code (e.g., rog, asus)")


class KBInfo(BaseModel):
    """Knowledge base information."""

    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """Tech agent API output model."""

    answer: str = Field(default="", description="Answer content")
    ask_flag: bool = Field(
        default=False, description="Whether to ask for clarification"
    )
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint candidates"
    )
    kb: KBInfo = Field(
        default_factory=KBInfo, description="Knowledge base information"
    )


class RenderOption(BaseModel):
    """Render option for frontend."""

    name: Optional[str] = None
    value: Optional[str] = None
    icon: Optional[str] = None
    answer: Optional[List[Dict[str, Any]]] = None
    type: Optional[str] = None
    cards: Optional[List[Dict[str, Any]]] = None


class RenderItem(BaseModel):
    """Render item for frontend."""

    renderId: str
    stream: bool = False
    type: str
    message: str
    remark: List[str] = Field(default_factory=list)
    option: List[Dict[str, Any]] = Field(default_factory=list)


class TechAgentResult(BaseModel):
    """Tech agent result structure."""

    renderTime: int
    render: List[RenderItem]


class TechAgentResponse(BaseModel):
    """Tech agent API response model."""

    status: int = Field(default=200, description="HTTP status code")
    message: str = Field(default="OK", description="Response message")
    result: Any = Field(
        default_factory=dict, description="Result data"
    )


class CosmosLogData(BaseModel):
    """Cosmos DB log data structure."""

    id: str
    cus_id: str
    session_id: str
    chat_id: str
    createDate: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str
    user_info: Dict[str, Any] = Field(default_factory=dict)
    process_info: Dict[str, Any] = Field(default_factory=dict)
    final_result: Dict[str, Any] = Field(default_factory=dict)
    extract: Dict[str, Any] = Field(default_factory=dict)
    total_time: float
