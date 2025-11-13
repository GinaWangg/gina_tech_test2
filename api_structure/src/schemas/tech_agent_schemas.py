"""
Pydantic schemas for tech_agent endpoint.
Defines request/response models and internal data structures.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型"""

    cus_id: str = Field(..., description="Customer ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: str = Field(..., description="Chat ID")
    user_input: str = Field(..., description="User input message")
    websitecode: str = Field(..., description="Website code (e.g., 'tw')")
    product_line: str = Field(..., description="Product line")
    system_code: str = Field(..., description="System code (e.g., 'rog')")


class KBInfo(BaseModel):
    """Knowledge Base information"""

    kb_no: str = Field(default="", description="KB number")
    title: str = Field(default="", description="KB title")
    similarity: float = Field(default=0.0, description="Similarity score")
    source: str = Field(default="", description="Response source")
    exec_time: float = Field(default=0.0, description="Execution time")


class TechAgentOutput(BaseModel):
    """技術支援 API 輸出模型"""

    answer: str = Field(default="", description="Answer text")
    ask_flag: bool = Field(default=False, description="Whether asking question")
    hint_candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hint candidates"
    )
    kb: KBInfo = Field(default_factory=KBInfo, description="KB information")


class TechAgentResponse(BaseModel):
    """Complete API response"""

    status: int = Field(..., description="HTTP status code")
    type: Optional[str] = Field(None, description="Response type")
    message: str = Field(..., description="Response message")
    output: Optional[TechAgentOutput] = Field(
        None, description="Output data"
    )
    result: Optional[Any] = Field(None, description="Result data for rendering")


class RenderItem(BaseModel):
    """Individual render item"""

    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any] = Field(default_factory=list)
    option: List[Any] = Field(default_factory=list)


class RenderResult(BaseModel):
    """Render result structure"""

    renderTime: int
    render: List[RenderItem]


class UserInfo(BaseModel):
    """User information extracted from conversation"""

    our_brand: Optional[str] = "ASUS"
    location: Optional[str] = None
    main_product_category: Optional[str] = None
    sub_product_category: Optional[str] = None
    first_time: bool = True


class ProcessInfo(BaseModel):
    """Processing information for logging"""

    bot_scope: Optional[str] = None
    search_info: Optional[str] = None
    is_follow_up: bool = False
    faq_pl: Dict[str, Any] = Field(default_factory=dict)
    faq_wo_pl: Dict[str, Any] = Field(default_factory=dict)
    language: Optional[str] = None
    last_info: Dict[str, Any] = Field(default_factory=dict)


class CosmosLogData(BaseModel):
    """Data structure for Cosmos DB logging"""

    id: str
    cus_id: str
    session_id: str
    chat_id: str
    createDate: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str
    user_info: Dict[str, Any]
    process_info: ProcessInfo
    final_result: Dict[str, Any]
    extract: Dict[str, Any]
    total_time: float
