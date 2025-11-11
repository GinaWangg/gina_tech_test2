"""Pydantic models for tech agent API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TechAgentRequest(BaseModel):
    """Request model for tech agent endpoint."""
    
    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User's input/question")
    websitecode: str = Field(..., description="Website code (e.g., 'tw')")
    product_line: str = Field(
        default="", 
        description="Product line (empty if unknown)"
    )
    system_code: str = Field(..., description="System code (e.g., 'rog')")


class OptionAnswer(BaseModel):
    """Answer model for option."""
    
    type: str
    value: Any


class Option(BaseModel):
    """Option model for user interaction."""
    
    name: str
    value: str
    icon: Optional[str] = None
    type: Optional[str] = None
    cards: Optional[List[Dict[str, Any]]] = None
    answer: Optional[List[OptionAnswer]] = None


class RenderItem(BaseModel):
    """Individual render item in response."""
    
    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any] = []
    option: List[Option] = []


class TechAgentResponse(BaseModel):
    """Response model for tech agent endpoint."""
    
    status: int
    message: str
    result: List[RenderItem]


class UserInfo(BaseModel):
    """User information model."""
    
    main_product_category: Optional[str] = None
    sub_product_category: Optional[str] = None


class LastInfo(BaseModel):
    """Last interaction information."""
    
    prev_q: str
    prev_a: str
    kb_no: str


class ProcessInfo(BaseModel):
    """Process information model."""
    
    bot_scope: Optional[str] = None
    search_info: Optional[str] = None
    is_follow_up: bool = False
    faq_pl: Dict[str, Any] = {}
    faq_wo_pl: Dict[str, Any] = {}
    language: Optional[str] = None
    last_info: LastInfo


class KBInfo(BaseModel):
    """Knowledge base information."""
    
    kb_no: str
    title: str = ""
    similarity: float
    source: str = ""
    exec_time: float = 0.0


class ExtractOutput(BaseModel):
    """Extract output model."""
    
    answer: str
    ask_flag: bool
    hint_candidates: List[Any] = []
    kb: KBInfo


class Extract(BaseModel):
    """Extract information model."""
    
    status: int
    type: str
    message: str
    output: ExtractOutput


class CosmosData(BaseModel):
    """Cosmos DB data model for logging."""
    
    id: str
    cus_id: str
    session_id: str
    chat_id: str
    createDate: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str
    user_info: UserInfo
    process_info: ProcessInfo
    final_result: TechAgentResponse
    extract: Extract
    total_time: float
