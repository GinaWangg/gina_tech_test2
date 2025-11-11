"""Pydantic models for tech agent API."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型."""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User question or input")
    websitecode: str = Field(..., description="Website code (e.g., 'tw', 'us')")
    product_line: str = Field(
        "", description="Product line (empty if not specified)"
    )
    system_code: str = Field(..., description="System code (e.g., 'rog', 'asus')")


class KBInfo(BaseModel):
    """Knowledge base information model."""

    kb_no: str = Field("", description="Knowledge base number")
    title: str = Field("", description="KB article title")
    similarity: float = Field(0.0, description="Similarity score")
    source: str = Field("", description="Response source")
    exec_time: float = Field(0.0, description="Execution time in seconds")


class HintCandidate(BaseModel):
    """Hint candidate model for product line suggestions."""

    title: str = Field(..., description="Product line title")
    title_name: str = Field(..., description="Display name")
    icon: str = Field(..., description="Icon URL")
    question: str = Field(..., description="Suggested question")


class TechAgentOutput(BaseModel):
    """技術支援 API 輸出模型."""

    answer: str = Field("", description="Generated answer")
    ask_flag: bool = Field(False, description="Whether follow-up is needed")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint suggestions"
    )
    kb: KBInfo = Field(default_factory=KBInfo, description="KB information")


class TechAgentResponse(BaseModel):
    """完整的技術支援 API 回應."""

    status: int = Field(200, description="HTTP status code")
    type: str = Field("answer", description="Response type")
    message: str = Field("OK", description="Response message")
    output: TechAgentOutput = Field(
        default_factory=TechAgentOutput, description="Output data"
    )
