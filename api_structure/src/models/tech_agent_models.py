"""Data models for tech agent API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TechAgentRequest(BaseModel):
    """Technical support API request model."""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User input message")
    websitecode: str = Field(..., description="Website code (e.g., 'tw')")
    product_line: str = Field(default="", description="Product line")
    system_code: str = Field(..., description="System code (e.g., 'rog')")


class KnowledgeBase(BaseModel):
    """Knowledge base information."""

    kb_no: str = Field(default="", description="Knowledge base number")
    title: str = Field(default="", description="Article title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class RenderOption(BaseModel):
    """Render option for response."""

    name: Optional[str] = Field(default=None, description="Option name")
    value: Optional[str] = Field(default=None, description="Option value")
    icon: Optional[str] = Field(default=None, description="Option icon")
    type: Optional[str] = Field(default=None, description="Option type")
    cards: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="FAQ cards"
    )
    answer: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Answer data"
    )


class RenderItem(BaseModel):
    """Individual render item in response."""

    renderId: str = Field(..., description="Render ID")
    stream: bool = Field(default=False, description="Is streaming response")
    type: str = Field(..., description="Render type")
    message: str = Field(..., description="Message content")
    remark: List[str] = Field(default_factory=list, description="Remarks")
    option: List[RenderOption] = Field(
        default_factory=list, description="Options"
    )


class TechAgentResponse(BaseModel):
    """Technical support API response model."""

    status: int = Field(..., description="Response status code")
    message: str = Field(..., description="Response message")
    result: List[RenderItem] = Field(
        default_factory=list, description="Render results"
    )
