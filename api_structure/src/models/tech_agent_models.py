"""Pydantic models for tech agent API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """Tech agent API input model."""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User input text")
    websitecode: str = Field(..., description="Website code")
    product_line: str = Field(default="", description="Product line")
    system_code: str = Field(..., description="System code")


class KBInfo(BaseModel):
    """Knowledge base information."""

    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class HintCandidate(BaseModel):
    """Hint candidate model."""

    title_name: str = Field(..., description="Title name")
    title: str = Field(..., description="Title")
    icon: str = Field(default="", description="Icon")
    question: Optional[str] = Field(
        None, description="Associated question"
    )


class TechAgentOutput(BaseModel):
    """Tech agent API output model."""

    answer: str = Field(default="", description="Answer text")
    ask_flag: bool = Field(default=False, description="Ask flag")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint candidates"
    )
    kb: KBInfo = Field(
        default_factory=KBInfo, description="KB information"
    )


class TechAgentResponse(BaseModel):
    """Tech agent API response model."""

    status: int = Field(..., description="HTTP status code")
    type: str = Field(
        default="", description="Response type (reask/answer/handoff)"
    )
    message: str = Field(..., description="Response message")
    output: TechAgentOutput = Field(..., description="Output data")


class RenderOption(BaseModel):
    """Render option model."""

    name: Optional[str] = None
    value: Optional[str] = None
    icon: Optional[str] = None
    type: Optional[str] = None
    cards: Optional[List[Dict[str, Any]]] = None
    answer: Optional[List[Dict[str, Any]]] = None


class RenderItem(BaseModel):
    """Render item model."""

    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any] = Field(default_factory=list)
    option: List[Any] = Field(default_factory=list)


class FinalResult(BaseModel):
    """Final result model."""

    status: int
    message: str
    result: List[RenderItem] | Dict[str, Any]
