"""
Tech Agent API request and response schemas.
Maintains exact compatibility with original implementation.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型"""
    cus_id: str
    session_id: str
    chat_id: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str


class KbInfo(BaseModel):
    """Knowledge base information"""
    kb_no: str = ""
    title: str = ""
    similarity: float = 0.0
    source: str = ""
    exec_time: float = 0.0


class TechAgentOutput(BaseModel):
    """Tech agent response output"""
    answer: str
    ask_flag: bool
    hint_candidates: List[Dict[str, Any]]
    kb: KbInfo


class RenderOption(BaseModel):
    """Render option model"""
    name: Optional[str] = None
    value: Optional[str] = None
    icon: Optional[str] = None
    type: Optional[str] = None
    cards: Optional[List[Dict[str, Any]]] = None
    answer: Optional[List[Dict[str, Any]]] = None


class RenderItem(BaseModel):
    """Individual render item"""
    renderId: str
    stream: bool
    type: str
    message: str
    remark: List[Any]
    option: List[Dict[str, Any]]


class TechAgentFinalResult(BaseModel):
    """Final result structure matching original output"""
    status: int
    message: str
    result: List[RenderItem]


class TechAgentResponseData(BaseModel):
    """Response data structure for logging"""
    status: int
    type: str
    message: str
    output: TechAgentOutput
