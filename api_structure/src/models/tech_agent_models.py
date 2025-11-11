"""Pydantic models for tech agent API."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TechAgentInput(BaseModel):
    """Input model for tech agent API request."""

    cus_id: str
    session_id: str
    chat_id: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str


class UserInfo(BaseModel):
    """User information model."""

    our_brand: str = "ASUS"
    location: Optional[str] = None
    main_product_category: Optional[str] = None
    sub_product_category: Optional[str] = None
    first_time: bool = True


class KBInfo(BaseModel):
    """Knowledge base information model."""

    kb_no: str
    title: str
    similarity: float
    source: str
    exec_time: float


class HintCandidate(BaseModel):
    """Hint candidate model for product line re-ask."""

    title: str
    title_name: str
    icon: str
    question: str


class TechAgentOutput(BaseModel):
    """Output model for tech agent API response."""

    status: int
    type: str
    message: str
    output: Dict[str, Any]


class RenderItem(BaseModel):
    """Render item for final response."""

    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any]
    option: List[Any]


class TechAgentResponse(BaseModel):
    """Final response model for tech agent API."""

    status: int
    message: str
    result: List[Dict[str, Any]]
