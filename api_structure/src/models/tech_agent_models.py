"""Data models for tech agent API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型.
    
    Attributes:
        cus_id: Customer ID
        session_id: Session identifier
        chat_id: Chat identifier
        user_input: User's question or input
        websitecode: Website code (e.g., 'tw', 'us')
        product_line: Product line identifier
        system_code: System code identifier
    """

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session identifier")
    chat_id: str = Field(..., description="Chat identifier")
    user_input: str = Field(..., description="User's question or input")
    websitecode: str = Field(..., description="Website code")
    product_line: str = Field(..., description="Product line identifier")
    system_code: str = Field(..., description="System code identifier")


class KBInfo(BaseModel):
    """Knowledge base information.
    
    Attributes:
        kb_no: Knowledge base number
        title: KB article title
        similarity: Similarity score
        source: Response source
        exec_time: Execution time in seconds
    """

    kb_no: str = Field(default="", description="Knowledge base number")
    title: str = Field(default="", description="KB article title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """技術支援 API 輸出模型.
    
    Attributes:
        answer: Generated answer
        ask_flag: Whether follow-up question is needed
        hint_candidates: List of suggestion hints
        kb: Knowledge base information
    """

    answer: str = Field(default="", description="Generated answer")
    ask_flag: bool = Field(default=False, description="Follow-up needed")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Suggestion hints"
    )
    kb: KBInfo = Field(
        default_factory=KBInfo, description="Knowledge base info"
    )


class RenderItem(BaseModel):
    """Render item for frontend display.
    
    Attributes:
        renderId: Unique render identifier
        stream: Whether streaming is enabled
        type: Render type
        message: Message to display
        remark: Additional remarks
        option: Display options
    """

    renderId: str = Field(..., description="Render identifier")
    stream: bool = Field(default=False, description="Streaming enabled")
    type: str = Field(..., description="Render type")
    message: str = Field(..., description="Message to display")
    remark: List[Any] = Field(default_factory=list, description="Remarks")
    option: List[Dict[str, Any]] = Field(
        default_factory=list, description="Display options"
    )


class TechAgentResponse(BaseModel):
    """完整的技術支援 API 回應.
    
    Attributes:
        status: HTTP status code
        message: Response message
        result: Rendered result items or output data
    """

    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")
    result: Optional[Any] = Field(
        default=None, description="Result data"
    )
