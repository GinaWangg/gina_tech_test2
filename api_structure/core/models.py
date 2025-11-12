"""Pydantic models for tech agent API."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TechAgentInput(BaseModel):
    """Input model for tech agent API endpoint.
    
    Attributes:
        cus_id: Customer ID.
        session_id: Session identifier.
        chat_id: Chat identifier.
        user_input: User's input message.
        websitecode: Website code (e.g., 'tw').
        product_line: Product line category.
        system_code: System code (e.g., 'rog').
    """
    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session identifier")
    chat_id: str = Field(..., description="Chat identifier")
    user_input: str = Field(..., description="User's input message")
    websitecode: str = Field(..., description="Website code")
    product_line: str = Field(default="", description="Product line category")
    system_code: str = Field(..., description="System code")


class KBInfo(BaseModel):
    """Knowledge base information.
    
    Attributes:
        kb_no: Knowledge base number.
        title: KB article title.
        similarity: Similarity score.
        source: Response source.
        exec_time: Execution time in seconds.
    """
    kb_no: str = Field(default="", description="Knowledge base number")
    title: str = Field(default="", description="KB article title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """Output model for tech agent response.
    
    Attributes:
        answer: Generated answer text.
        ask_flag: Whether follow-up question is needed.
        hint_candidates: List of suggested follow-up questions.
        kb: Knowledge base information.
    """
    answer: str = Field(default="", description="Generated answer")
    ask_flag: bool = Field(default=False, description="Follow-up flag")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested questions"
    )
    kb: KBInfo = Field(default_factory=KBInfo, description="KB info")


class TechAgentResponse(BaseModel):
    """Complete response model for tech agent API.
    
    Attributes:
        status: HTTP status code.
        type: Response type.
        message: Response message.
        output: Response output data.
    """
    status: int = Field(default=200, description="HTTP status code")
    type: str = Field(default="answer", description="Response type")
    message: str = Field(default="OK", description="Response message")
    output: TechAgentOutput = Field(
        default_factory=TechAgentOutput,
        description="Response data"
    )
