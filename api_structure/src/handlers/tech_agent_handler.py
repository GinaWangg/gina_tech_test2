"""Tech Agent Handler - Core business logic for technical support.

This module contains the TechAgentHandler class which orchestrates
the entire technical support flow including:
- Chat history processing
- User info extraction
- Knowledge base search
- Response generation
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from api_structure.core.logger import set_extract_log
from api_structure.core.timer import timed
from api_structure.src.clients.mock_container_client import (
    MockChatFlow,
    MockDependencyContainer,
    MockServiceProcess,
)
from api_structure.src.handlers.response_generator import ResponseGenerator
from api_structure.src.models.tech_agent_models import TechAgentInput

# Constants
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for technical support agent processing.

    This is the main entry point for processing tech agent requests.
    The class orchestrates the flow but delegates specific tasks to
    focused helper methods and components.
    """

    def __init__(self, container: MockDependencyContainer, user_input: TechAgentInput):
        """Initialize the tech agent handler.

        Args:
            container: Dependency container with all services
            user_input: User input data
        """
        self.containers = container
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Core components
        self.chat_flow: Optional[MockChatFlow] = None
        self.service_process: Optional[MockServiceProcess] = None
        self.response_generator: Optional[ResponseGenerator] = None

        # State variables
        self._init_state_variables()

    def _init_state_variables(self) -> None:
        """Initialize state variables for the handler."""
        self.his_inputs: Optional[List[str]] = None
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Optional[Dict] = None
        self.last_hint: Optional[Dict] = None
        self.is_follow_up: bool = False
        self.lang: Optional[str] = None
        self.chat_count: int = 0
        self.user_info_dict: Dict = {}
        self.bot_scope_chat: Optional[str] = None
        self.search_info: Optional[str] = None
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List[str] = []
        self.faqs_wo_pl: List[Dict] = []
        self.type: str = ""
        self.renderId: str = ""

    @timed(task_name="tech_agent_process")
    async def run(self) -> Dict[str, Any]:
        """Main entry point for processing tech agent requests.

        This is the primary method that orchestrates the entire flow.

        Returns:
            Response dictionary with status, message, and result
        """
        self._log_input()

        # Initialize components
        await self._initialize()

        # Process request
        await self._process_request()

        # Generate and return response
        result = await self._generate_final_response()

        # Log results
        await self._log_results(result)

        return result

    def _log_input(self) -> None:
        """Log incoming request."""
        log_json = json.dumps(
            self.user_input.model_dump(), ensure_ascii=False, indent=2
        )
        print(f"\n[Agent 啟動] 輸入內容: {log_json}")

    async def _initialize(self) -> None:
        """Initialize all required components and data."""
        await self._initialize_chat()
        self.renderId = str(uuid.uuid4())

        # Initialize response generator
        self.response_generator = ResponseGenerator(
            service_process=self.service_process,
            chat_flow=self.chat_flow,
            user_input=self.user_input,
            render_id=self.renderId,
            lang=self.lang,
        )

    async def _process_request(self) -> None:
        """Process the user request through the pipeline."""
        await self._process_history()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()
        self._check_follow_up()

    def _check_follow_up(self) -> None:
        """Check if this is a follow-up question."""
        self.is_follow_up = False
        print(f"是否延續問題追問 : {self.is_follow_up}")

    async def _generate_final_response(self) -> Dict[str, Any]:
        """Generate the final response based on processed data.

        Returns:
            Final response dictionary
        """
        if not self.bot_scope_chat:
            return await self.response_generator.generate_no_product_line_response(
                his_inputs=self.his_inputs,
                faqs_wo_pl=self.faqs_wo_pl,
                search_info=self.search_info,
                containers=self.containers,
            )
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            return await self.response_generator.generate_high_similarity_response(
                top4_kb_list=self.top4_kb_list,
                top1_kb=self.top1_kb,
                top1_kb_sim=self.top1_kb_sim,
                search_info=self.search_info,
                his_inputs=self.his_inputs,
                containers=self.containers,
            )
        else:
            return await self.response_generator.generate_low_similarity_response(
                top1_kb=self.top1_kb,
                top1_kb_sim=self.top1_kb_sim,
                his_inputs=self.his_inputs,
                kb_mappings=self.containers.KB_mappings,
            )

    async def _log_results(self, result: Dict[str, Any]) -> None:
        """Log and save results to storage.

        Args:
            result: The final result dictionary
        """
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        print(f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n")

        cosmos_data = self._build_cosmos_data(result, exec_time)
        await self.containers.cosmos_settings.insert_data(cosmos_data)

        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        print(f"\n[Cosmos DB] 寫入資料: {log_json}\n")

        # Set extract log for middleware
        set_extract_log(self.response_generator.response_data)

    def _build_cosmos_data(self, result: Dict[str, Any], exec_time: float) -> Dict:
        """Build Cosmos DB data structure.

        Args:
            result: Final result dictionary
            exec_time: Execution time in seconds

        Returns:
            Cosmos data dictionary
        """
        return {
            "id": (
                f"{self.user_input.cus_id}-{self.user_input.session_id}-"
                f"{self.user_input.chat_id}"
            ),
            "cus_id": self.user_input.cus_id,
            "session_id": self.user_input.session_id,
            "chat_id": self.user_input.chat_id,
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": self.user_input.user_input,
            "websitecode": self.user_input.websitecode,
            "product_line": self.user_input.product_line,
            "system_code": self.user_input.system_code,
            "user_info": self.user_info_dict,
            "process_info": {
                "bot_scope": self.bot_scope_chat,
                "search_info": self.search_info,
                "is_follow_up": self.is_follow_up,
                "faq_pl": self.faq_result,
                "faq_wo_pl": self.faq_result_wo_pl,
                "language": self.lang,
            },
            "final_result": result,
            "extract": self.response_generator.response_data,
            "total_time": exec_time,
        }

    async def _initialize_chat(self) -> None:
        """Initialize chat, retrieve history and basic info.

        # TODO: Enable when environment ready
        # This would query Cosmos DB for real chat history
        """
        settings = self.containers.cosmos_settings

        # Get messages, hint, and language
        results = await settings.create_GPT_messages(
            self.user_input.session_id, self.user_input.user_input
        )
        self.last_hint = await settings.get_latest_hint(self.user_input.session_id)
        self.lang = await settings.get_language_by_websitecode_dev(
            self.user_input.websitecode
        )

        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output,
        ) = results

        log_json = json.dumps(
            {
                "his_inputs": self.his_inputs,
                "chat_count": self.chat_count,
                "user_info": self.user_info,
                "last_bot_scope": self.last_bot_scope,
            },
            ensure_ascii=False,
            indent=2,
        )
        print(f"\n[歷史對話]\n{log_json}")

        # Generate IDs if missing
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())

        print(f"last_hint: {self.last_hint}")

        # Initialize services
        self.service_process = MockServiceProcess(
            system_code=self.user_input.system_code, container=self.containers
        )
        self.chat_flow = MockChatFlow(
            data=self.user_input,
            last_hint=self.last_hint,
            container=self.containers,
        )

        if not self.user_info:
            self.user_info = self.chat_flow.default_user_info
        if (
            self.user_input.product_line
            and self.last_bot_scope != self.user_input.product_line
        ):
            self.user_info["main_product_category"] = self.user_input.product_line
            self.user_info["first_time"] = True

    async def _process_history(self) -> None:
        """Process chat history.

        # TODO: Enable when environment ready
        # This would call real sentence grouping API
        """
        if len(self.his_inputs) <= 1:
            print(f"his_inputs : {self.his_inputs}")
            return

        # Mock: Simple grouping
        group_task = self.containers.sentence_group_classification
        results_related = await group_task.sentence_group_classification(
            self.his_inputs
        )

        # Process grouping results
        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = groups[-1].get("statements") or []
            latest_group_statements = [s for s in statements if isinstance(s, str)]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        print(f"last group statements => {self.his_inputs[-1]}")
        print(f"his_inputs : {self.his_inputs}")

    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope.

        # TODO: Enable when environment ready
        # This would call real GPT APIs for extraction
        """
        # Get user info
        result_user_info = await self.chat_flow.get_userInfo(his_inputs=self.his_inputs)
        self.user_info_dict = result_user_info[0]

        # Get search info
        search_info_result = await self.chat_flow.get_searchInfo(self.his_inputs)

        # Check tech support related (mocked)
        tech_support_related = "true"
        if self.last_hint and self.last_hint.get("hintType") == "productline-reask":
            # TODO: Enable when environment ready
            # prompt = [{"role": "user", "content": prompt_content}]
            # tech_support_related = await self.chat_flow.container.base_service.GPT41_mini_response(prompt)  # noqa: E501
            pass

        log_json = json.dumps(self.user_info_dict, ensure_ascii=False, indent=2)
        print(f"\n[使用者資訊]\n{log_json}")

        # Determine search_info
        if tech_support_related == "false" and self.last_hint:
            self.search_info = self.last_hint.get("searchInfo")
        else:
            self.search_info = search_info_result

        # Get bot_scope
        self.bot_scope_chat = (
            self.user_input.product_line
            or await self.chat_flow.get_bot_scope_chat(
                prev_user_info=self.user_info,
                curr_user_info=self.user_info_dict,
                last_bot_scope=self.last_bot_scope,
            )
        )

        print(f"\n[Bot Scope 判斷] {self.bot_scope_chat}")

    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line.

        # TODO: Enable when environment ready
        # This would call real Redis/Vector DB search
        """
        response = await self.containers.sd.service_discreminator_with_productline(
            user_question_english=self.search_info,
            site=self.user_input.websitecode,
            specific_kb_mappings=self.containers.specific_kb_mappings,
            productLine=self.bot_scope_chat,
        )
        log_json = json.dumps(response, ensure_ascii=False, indent=2)
        print(f"[ServiceDiscriminator] discrimination_productline_response: {log_json}")

        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    def _process_kb_results(self) -> None:
        """Process and filter results from KB search."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list) if sim >= KB_THRESHOLD
        ][:3]
        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0

        self.faqs_wo_pl = [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", []),
            )
        ]
