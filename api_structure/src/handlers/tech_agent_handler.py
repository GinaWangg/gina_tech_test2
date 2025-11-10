"""Handler for tech agent processing logic."""

import uuid
from typing import Dict, Any
from api_structure.core.timer import timed
from api_structure.core.logger import set_extract_log
from api_structure.src.models.tech_agent_models import (
    TechAgentRequest,
    RenderItem,
    RenderOption,
)


class TechAgentHandler:
    """Handler class for tech agent processing."""

    def __init__(self):
        """Initialize the tech agent handler."""
        self.render_id = str(uuid.uuid4())

    @timed(task_name="tech_agent_handler_process")
    async def process(self, request: TechAgentRequest) -> Dict[str, Any]:
        """
        Process tech agent request and generate response.

        This method simulates the tech agent processing flow.
        Due to permission issues, API and Cosmos DB calls are mocked with
        fixed responses.

        Args:
            request: Tech agent request data

        Returns:
            Dictionary containing processed results with render items
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

        # 根據產品線決定回應類型
        if not request.product_line:
            # 無產品線：返回產品線詢問
            return await self._handle_no_product_line(request)
        else:
            # 有產品線：返回技術支援回應
            return await self._handle_with_product_line(request)

    @timed(task_name="tech_agent_handler_no_product_line")
    async def _handle_no_product_line(
        self, request: TechAgentRequest
    ) -> Dict[str, Any]:
        """
        Handle request without product line.

        模擬產品線追問流程。
        實際應調用：
        - service_process.technical_support_productline_reask()
        - cosmos_settings.insert_hint_data()

        Args:
            request: Tech agent request

        Returns:
            Response with product line options
        """
        # TODO: 實際應執行以下邏輯（目前因權限問題使用固定回應）
        # reask_result = await service_process.technical_support_productline_reask(
        #     user_input=request.user_input,
        #     faqs_wo_pl=faqs_wo_pl,
        #     site=request.websitecode,
        #     lang=lang,
        #     system_code=request.system_code,
        # )

        # 固定的產品線選項（模擬回應）
        product_line_options = [
            {
                "name": "筆記型電腦",
                "value": "notebook",
                "icon": "laptop",
            },
            {
                "name": "桌上型電腦",
                "value": "desktop",
                "icon": "desktop",
            },
            {
                "name": "手機",
                "value": "phone",
                "icon": "phone",
            },
        ]

        render_item = RenderItem(
            renderId=self.render_id,
            stream=False,
            type="avatarAskProductLine",
            message=(
                "我注意到你提到的問題，為了給你最準確的協助，"
                "能告訴我是哪個產品類別嗎？"
            ),
            remark=[],
            option=[
                RenderOption(**opt) for opt in product_line_options
            ],
        )

        return {"render_items": [render_item]}

    @timed(task_name="tech_agent_handler_with_product_line")
    async def _handle_with_product_line(
        self, request: TechAgentRequest
    ) -> Dict[str, Any]:
        """
        Handle request with product line specified.

        模擬技術支援流程。
        實際應調用：
        - service_discriminator_with_productline()
        - technical_support_hint_create()
        - reply_with_faq_gemini_sys_avatar()

        Args:
            request: Tech agent request

        Returns:
            Response with technical support information
        """
        # TODO: 實際應執行以下邏輯（目前因權限問題使用固定回應）
        # 1. 搜尋知識庫
        # response = await service_discriminator.service_discreminator_with_productline(
        #     user_question_english=search_info,
        #     site=request.websitecode,
        #     specific_kb_mappings=containers.specific_kb_mappings,
        #     productLine=request.product_line,
        # )
        #
        # 2. 生成 RAG 回應
        # rag_response = await service_process.technical_support_hint_create(...)
        #
        # 3. 生成 Avatar 回應
        # avatar_response = await ts_rag.reply_with_faq_gemini_sys_avatar(...)

        # 模擬技術支援回應（固定回應）
        mock_kb_content = {
            "link": "https://www.asus.com/support/FAQ/1234567/",
            "title": "如何解決筆電登入畫面卡住的問題",
            "content": (
                "請嘗試以下步驟：\n"
                "1. 長按電源鍵強制關機\n"
                "2. 重新開機並進入安全模式\n"
                "3. 檢查是否有系統更新"
            ),
        }

        # 技術支援回應
        render_item = RenderItem(
            renderId=self.render_id,
            stream=False,
            type="avatarTechnicalSupport",
            message=(
                "根據你的描述，這可能是系統啟動時的暫時性問題。"
                "我建議你先嘗試強制重啟，並檢查是否有可用的系統更新。"
            ),
            remark=[],
            option=[
                RenderOption(
                    type="faqcards",
                    cards=[mock_kb_content],
                )
            ],
        )

        return {"render_items": [render_item]}
