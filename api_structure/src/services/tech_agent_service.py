"""
Tech Agent Service - Business logic layer for tech agent operations.
Orchestrates between handlers and repositories, preserving original business logic.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from api_structure.core.logger import logger
from api_structure.src.repositories.tech_agent_repository import TechAgentRepository


TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentService:
    """Service layer for tech agent business logic."""
    
    def __init__(self, repository: TechAgentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: TechAgentRepository instance
        """
        self.repository = repository
    
    def generate_render_id(self) -> str:
        """Generate a unique render ID."""
        return str(uuid.uuid4())
    
    def ensure_session_and_chat_ids(
        self, 
        session_id: str, 
        chat_id: str, 
        cus_id: str
    ) -> Tuple[str, str, str]:
        """
        Ensure session_id, chat_id, and cus_id have valid values.
        
        Args:
            session_id: Session identifier
            chat_id: Chat identifier
            cus_id: Customer identifier
        
        Returns:
            Tuple of (session_id, chat_id, cus_id)
        """
        if not session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            session_id = f"agent-{tail}"
        
        if not cus_id:
            cus_id = "test"
        
        if not chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            chat_id = f"agent-{tail}"
        
        return session_id, chat_id, cus_id
    
    def process_kb_results(
        self, 
        faq_result: Dict[str, Any]
    ) -> Tuple[List[str], Optional[str], float]:
        """
        Process and filter results from KB search.
        
        Args:
            faq_result: FAQ search results
        
        Returns:
            Tuple of (top4_kb_list, top1_kb, top1_kb_sim)
        """
        faq_list = faq_result.get("faq", [])
        sim_list = faq_result.get("cosineSimilarity", [])
        
        top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list) if sim >= KB_THRESHOLD
        ][:3]
        
        top1_kb = faq_list[0] if faq_list else None
        top1_kb_sim = sim_list[0] if sim_list else 0.0
        
        return top4_kb_list, top1_kb, top1_kb_sim
    
    def prepare_faqs_wo_pl(
        self, 
        faq_result_wo_pl: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prepare FAQ results without product line.
        
        Args:
            faq_result_wo_pl: FAQ results without product line filter
        
        Returns:
            List of FAQ items with metadata
        """
        return [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                faq_result_wo_pl.get("faq", []),
                faq_result_wo_pl.get("cosineSimilarity", []),
                faq_result_wo_pl.get("productLine", []),
            )
        ]
    
    def build_no_product_line_response(
        self,
        render_id: str,
        avatar_message: str,
        relative_questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build response for no product line case.
        
        Args:
            render_id: Unique render identifier
            avatar_message: Avatar response message
            relative_questions: List of related questions
        
        Returns:
            Complete response dictionary
        """
        return {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": render_id,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": avatar_message,
                    "remark": [],
                    "option": [
                        {
                            "name": item["title_name"],
                            "value": item["title"],
                            "icon": item["icon"]
                        }
                        for item in relative_questions
                    ]
                }
            ]
        }
    
    def build_high_similarity_response(
        self,
        render_id: str,
        avatar_message: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build response for high similarity case.
        
        Args:
            render_id: Unique render identifier
            avatar_message: Avatar response message
            content: RAG content dictionary
        
        Returns:
            Complete response dictionary
        """
        return {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": render_id,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": avatar_message,
                    "remark": [],
                    "option": [
                        {
                            "type": "faqcards",
                            "cards": [
                                {
                                    "link": content.get("link", ""),
                                    "title": content.get("title", ""),
                                    "content": content.get("content", ""),
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def build_low_similarity_response(
        self,
        render_id: str,
        avatar_message: str
    ) -> Dict[str, Any]:
        """
        Build response for low similarity case (handoff to human).
        
        Args:
            render_id: Unique render identifier
            avatar_message: Avatar response message
        
        Returns:
            Complete response dictionary
        """
        return {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": render_id,
                    "stream": False,
                    "type": "avatarText",
                    "message": avatar_message,
                    "remark": [],
                    "option": []
                },
                {
                    "renderId": render_id,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱～比如「ROG Flow X16」或「我想查產品保固到期日」。給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！",
                    "remark": [],
                    "option": [
                        {
                            "name": "我想知道 ROG FLOW X16 的規格",
                            "value": "我想知道 ROG FLOW X16 的規格",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent"
                                },
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation"
                                },
                                {
                                    "type": "mainProduct",
                                    "value": 25323
                                }
                            ]
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent"
                                },
                                {
                                    "type": "inquireKey",
                                    "value": "purchasing-recommendation-of-asus-products"
                                }
                            ]
                        },
                        {
                            "name": "請幫我介紹 ROG Phone 8 的特色",
                            "value": "請幫我介紹 ROG Phone 8 的特色",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent"
                                },
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation"
                                },
                                {
                                    "type": "mainProduct",
                                    "value": 25323
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def build_response_data(
        self,
        status: int,
        response_type: str,
        message: str,
        output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build response data for logging.
        
        Args:
            status: HTTP status code
            response_type: Type of response (reask, answer, handoff)
            message: Response message
            output: Output data
        
        Returns:
            Response data dictionary
        """
        return {
            "status": status,
            "type": response_type,
            "message": message,
            "output": output
        }
