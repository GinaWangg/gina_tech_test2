"""Handler for tech agent processing logic."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict

from api_structure.core.logger import set_extract_log
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentRequest


class TechAgentHandler:
    """Handler class for tech agent processing."""

    def __init__(self, containers):
        """
        Initialize the tech agent handler.

        Args:
            containers: DependencyContainer with all required services
        """
        self.containers = containers
        self.start_time = time.perf_counter()
        self.render_id = str(uuid.uuid4())

    @timed(task_name="tech_agent_handler_process")
    async def process(self, request: TechAgentRequest) -> Dict[str, Any]:
        """
        Process tech agent request with mocked responses.

        Due to permission issues, API and Cosmos DB calls are mocked.
        The structure follows the original TechAgentProcessor flow:
        1. Initialize chat and retrieve history
        2. Process user info and bot scope detection
        3. Search knowledge base
        4. Generate responses based on similarity

        Args:
            request: Tech agent request data

        Returns:
            Complete cosmos_data structure matching original format
        """
        # 記錄處理日誌
        set_extract_log(
            {
                "user_input": request.user_input,
                "session_id": request.session_id,
                "product_line": request.product_line,
                "system_code": request.system_code,
            }
        )

        # ===== 步驟 1: 初始化 chat（模擬）=====
        # 實際應執行：
        # - cosmos_settings.create_GPT_messages()
        # - cosmos_settings.get_latest_hint()
        # - cosmos_settings.get_language_by_websitecode_dev()
        # 模擬返回固定值
        lang = "zh-tw"
        his_inputs = [request.user_input]

        # ===== 步驟 2: 處理歷史對話（模擬）=====
        # 實際應執行：
        # - sentence_group_classification.sentence_group_classification()
        # - chat_flow.is_follow_up()
        # 模擬返回固定值
        is_follow_up = False

        # ===== 步驟 3: 取得用戶資訊和範圍（模擬）=====
        # 實際應執行：
        # - chat_flow.get_userInfo()
        # - chat_flow.get_searchInfo()
        # - chat_flow.get_bot_scope_chat()
        # 模擬返回固定值
        user_info_dict = {
            "main_product_category": "notebook",
            "sub_product_category": None,
        }
        search_info = (
            "my laptop is stuck on the login screen and "
            "there's no response at all."
        )
        bot_scope = "notebook"

        # ===== 步驟 4: 搜尋知識庫（模擬）=====
        # 實際應執行：
        # - service_discriminator.service_discreminator_with_productline()
        # 模擬返回固定的 FAQ 搜尋結果
        faq_result = {
            "faq": [1051479, 1038855, 1046480, 1042613],
            "cosineSimilarity": [
                0.816743731499,
                0.751851916313,
                0.701354265213,
                0.700322508812,
            ],
            "productLine": [
                "chromebook,desktop,gaming_handhelds,motherboard,notebook",
                "chromebook,desktop,gaming_handhelds,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,notebook",
            ],
        }
        faq_result_wo_pl = faq_result.copy()

        # 取得最高相似度的 KB
        top1_kb = faq_result["faq"][0] if faq_result["faq"] else None
        top1_kb_sim = (
            faq_result["cosineSimilarity"][0]
            if faq_result["cosineSimilarity"]
            else 0.0
        )

        # ===== 步驟 5: 生成回應（模擬）=====
        # 根據相似度決定回應類型
        # TOP1_KB_SIMILARITY_THRESHOLD = 0.87
        if top1_kb_sim < 0.87:
            # 相似度低，轉人工（avatarText + avatarAsk）
            # 實際應執行：
            # - ts_rag.reply_with_faq_gemini_sys_avatar()
            final_result, extract = self._create_low_similarity_response()
        else:
            # 相似度高，返回技術支援
            final_result, extract = self._create_high_similarity_response()

        # ===== 步驟 6: 建立完整的 cosmos_data（模擬）=====
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)

        cosmos_data = {
            "id": (f"{request.cus_id}-{request.session_id}-{request.chat_id}"),
            "cus_id": request.cus_id,
            "session_id": request.session_id,
            "chat_id": request.chat_id,
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": request.user_input,
            "websitecode": request.websitecode,
            "product_line": request.product_line,
            "system_code": request.system_code,
            "user_info": user_info_dict,
            "process_info": {
                "bot_scope": bot_scope,
                "search_info": search_info,
                "is_follow_up": is_follow_up,
                "faq_pl": faq_result,
                "faq_wo_pl": faq_result_wo_pl,
                "language": lang,
                "last_info": {
                    "prev_q": request.user_input,
                    "prev_a": "",
                    "kb_no": str(top1_kb) if top1_kb else "",
                },
            },
            "final_result": final_result,
            "extract": extract,
            "total_time": exec_time,
        }

        # 實際應執行：cosmos_settings.insert_data(cosmos_data)
        # 因權限問題，目前僅返回固定格式

        return cosmos_data

    def _create_low_similarity_response(self) -> tuple[Dict, Dict]:
        """
        Create response for low similarity case (handoff to human).

        模擬低相似度的回應，包含 avatarText 和 avatarAsk。
        實際應執行：ts_rag.reply_with_faq_gemini_sys_avatar()

        Returns:
            Tuple of (final_result, extract)
        """
        final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarText",
                    "message": "喔，筆電卡在登入畫面喔，這真的有點麻煩耶。嗯...",
                    "remark": [],
                    "option": [],
                },
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": (
                        "你可以告訴我像是產品全名、型號，或你想問的活動名稱～"
                        "比如「ROG Flow X16」或「我想查產品保固到期日」。"
                        "給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！"
                    ),
                    "remark": [],
                    "option": [
                        {
                            "name": "我想知道 ROG FLOW X16 的規格",
                            "value": "我想知道 ROG FLOW X16 的規格",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {"type": "mainProduct", "value": 25323},
                            ],
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": (
                                        "purchasing-recommendation-"
                                        "of-asus-products"
                                    ),
                                },
                            ],
                        },
                        {
                            "name": "請幫我介紹 ROG Phone 8 的特色",
                            "value": "請幫我介紹 ROG Phone 8 的特色",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {"type": "mainProduct", "value": 25323},
                            ],
                        },
                    ],
                },
            ],
        }

        extract = {
            "status": 200,
            "type": "handoff",
            "message": "相似度低，建議轉人工",
            "output": {
                "answer": "",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": "1051479",
                    "title": "",
                    "similarity": 0.816743731499,
                    "source": "",
                    "exec_time": 0.0,
                },
            },
        }

        return final_result, extract

    def _create_high_similarity_response(self) -> tuple[Dict, Dict]:
        """
        Create response for high similarity case (technical support).

        模擬高相似度的回應，包含技術支援和 FAQ 卡片。
        實際應執行：
        - technical_support_hint_create()
        - reply_with_faq_gemini_sys_avatar()

        Returns:
            Tuple of (final_result, extract)
        """
        final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": (
                        "根據你的描述，這可能是系統啟動時的暫時性問題。"
                        "我建議你先嘗試強制重啟，並檢查是否有可用的系統更新。"
                    ),
                    "remark": [],
                    "option": [
                        {
                            "type": "faqcards",
                            "cards": [
                                {
                                    "link": (
                                        "https://www.asus.com/support/"
                                        "FAQ/1051479/"
                                    ),
                                    "title": "如何解決筆電登入畫面卡住的問題",
                                    "content": (
                                        "請嘗試以下步驟：\n"
                                        "1. 長按電源鍵強制關機\n"
                                        "2. 重新開機並進入安全模式\n"
                                        "3. 檢查是否有系統更新"
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        extract = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": "請嘗試強制重啟並檢查系統更新",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": "1051479",
                    "title": "如何解決筆電登入畫面卡住的問題",
                    "similarity": 0.92,
                    "source": "knowledge_base",
                    "exec_time": 0.5,
                },
            },
        }

        return final_result, extract
