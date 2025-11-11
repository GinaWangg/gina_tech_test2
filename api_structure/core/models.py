"""Pydantic models for API request/response schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """Input model for tech agent API endpoint.
    
    Attributes:
        cus_id: Customer ID
        session_id: Session identifier
        chat_id: Chat identifier
        user_input: User's question or input text
        websitecode: Website code (e.g., 'tw', 'us')
        product_line: Product line category
        system_code: System code (e.g., 'rog', 'asus')
    """

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session identifier")
    chat_id: str = Field(..., description="Chat identifier")
    user_input: str = Field(..., description="User's question or input")
    websitecode: str = Field(..., description="Website code")
    product_line: str = Field(default="", description="Product line")
    system_code: str = Field(..., description="System code")


class TechAgentResponse(BaseModel):
    """Response model for tech agent API endpoint.
    
    Attributes:
        status: HTTP status code
        message: Response message
        result: Result data containing render information
    """

    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")
    result: Any = Field(..., description="Result data")


class KBInfo(BaseModel):
    """Knowledge Base information model.
    
    Attributes:
        kb_no: Knowledge base number
        title: KB article title
        similarity: Similarity score
        source: Response source
        exec_time: Execution time
    """

    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """Output data model for tech agent processing.
    
    Attributes:
        answer: Generated answer text
        ask_flag: Whether additional question is needed
        hint_candidates: List of suggested follow-up questions
        kb: Knowledge base information
    """

    answer: str = Field(default="", description="Generated answer")
    ask_flag: bool = Field(default=False, description="Ask flag")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint candidates"
    )
    kb: KBInfo = Field(default_factory=KBInfo, description="KB information")
