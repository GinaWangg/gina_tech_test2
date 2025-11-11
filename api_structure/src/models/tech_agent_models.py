"""Pydantic models for tech_agent endpoint."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TechAgentInput(BaseModel):
    """Input model for tech agent API."""
    
    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User's input text")
    websitecode: str = Field(..., description="Website code (e.g., 'tw')")
    product_line: str = Field(default="", description="Product line")
    system_code: str = Field(..., description="System code (e.g., 'rog')")


class KBInfo(BaseModel):
    """Knowledge base information."""
    
    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """Output model for tech agent API."""
    
    answer: str = Field(default="", description="Answer content")
    ask_flag: bool = Field(default=False, description="Ask flag")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of hint candidates"
    )
    kb: KBInfo = Field(
        default_factory=KBInfo,
        description="Knowledge base information"
    )


class TechAgentResponse(BaseModel):
    """Response model for tech agent API."""
    
    status: int = Field(..., description="HTTP status code")
    type: str = Field(default="", description="Response type")
    message: str = Field(..., description="Response message")
    output: TechAgentOutput = Field(
        default_factory=TechAgentOutput,
        description="Output data"
    )


class RenderItem(BaseModel):
    """Render item in final result."""
    
    renderId: str = Field(..., description="Render ID")
    stream: bool = Field(default=False, description="Stream flag")
    type: str = Field(..., description="Render type")
    message: str = Field(..., description="Message content")
    remark: List[Any] = Field(default_factory=list, description="Remarks")
    option: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Options"
    )


class FinalResult(BaseModel):
    """Final result structure."""
    
    renderTime: Optional[int] = Field(None, description="Render timestamp")
    render: List[RenderItem] = Field(
        default_factory=list,
        description="Render items"
    )


class TechAgentFinalResponse(BaseModel):
    """Final response model including render information."""
    
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")
    result: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Result list"
    )


class CosmosLogData(BaseModel):
    """Data structure for Cosmos DB logging."""
    
    id: str = Field(..., description="Document ID")
    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    createDate: str = Field(..., description="Creation timestamp")
    user_input: str = Field(..., description="User input")
    websitecode: str = Field(..., description="Website code")
    product_line: str = Field(..., description="Product line")
    system_code: str = Field(..., description="System code")
    user_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="User information"
    )
    process_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Process information"
    )
    final_result: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final result"
    )
    extract: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted data"
    )
    total_time: float = Field(..., description="Total execution time")


class __init__:
    """Package marker."""
    pass
