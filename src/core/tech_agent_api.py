import json
import time
import asyncio
import uuid
from datetime import datetime

from pydantic import BaseModel
from src.core.chat_flow import ChatFlow
from src.services.service_process import ServiceProcess
from utils.logger import logger

TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92

class TechAgentInput(BaseModel):
    cus_id :str
    session_id: str
    chat_id : str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str

class TechAgentProcessor:
    def __init__(self, containers, user_input: TechAgentInput):
        self.containers = containers
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Initialize attributes to be used across methods
        self.chat_flow = None
        self.service_process = None
        self.his_inputs = None
        self.user_info = None
        self.last_bot_scope = None
        self.last_extract_output = None
        self.last_hint = None
        self.is_follow_up = False
        self.lang = None
        self.chat_count = 0
        self.user_info_dict = {}
        self.bot_scope_chat = None
        self.search_info = None
        self.faq_result = {}
        self.faq_result_wo_pl = {}
        self.top1_kb = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list = []
        self.faqs_wo_pl = []
        self.response_data = {}

        self.type = ""
        self.avatar_response = ""
        self.avatar_process = None
        self.prev_q = ""
        self.prev_a = ""
        self.kb_no = ""
        self.content = ""
        self.result = []
        self.final_result = {}
        self.renderId = ""
        self.fu_task = None

    async def process(self, log_record: bool = True):
        """Main processing flow for the tech agent."""
        log_json = json.dumps(
            self.user_input.dict(), ensure_ascii=False, indent=2
        )
        logger.info(f"\n[Agent 啟動] 輸入內容: {log_json}")

        await self._initialize_chat()
        await self._process_history()
        self.avatar_process = asyncio.create_task(
            self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                self.his_inputs[-1], self.lang
                )
            )
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()

        follow_up = await self.fu_task if self.fu_task else {}
        self.is_follow_up = bool(follow_up.get("is_follow_up", False))
        logger.info(f"是否延續問題追問 : {self.is_follow_up}")
        
        await self._generate_response()

        if log_record:
            asyncio.create_task(self._log_and_save_results())

        return self.response_data

    async def process_stream(self):
        """Main processing flow with streaming support."""
        try:
            log_json = json.dumps(
                self.user_input.dict(), ensure_ascii=False, indent=2
            )
            logger.info(f"\n[Agent 啟動] 輸入內容: {log_json}")

            await self._initialize_chat()
            await self._process_history()
            self.avatar_process = asyncio.create_task(
                self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                    self.his_inputs[-1], self.lang
                )
            )
            await self._get_user_and_scope_info()
            await self._search_knowledge_base()
            self._process_kb_results()

            follow_up = await self.fu_task if self.fu_task else {}
            self.is_follow_up = bool(follow_up.get("is_follow_up", False))
            logger.info(f"是否延續問題追問 : {self.is_follow_up}")

            # Stream response generation
            if not self.bot_scope_chat:
                self.type = "avatarAskProductLine"
                async for event in self._handle_no_product_line_stream():
                    yield event
            elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
                self.type = "avatarTechnicalSupport"
                async for event in self._handle_high_similarity_stream():
                    yield event
            else:
                self.type = "avatarText"
                async for event in self._handle_low_similarity_stream():
                    yield event

            # Final save (不 stream，僅記錄)
            await self._log_and_save_results()

        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            yield {
                "status": 500,
                "message": f"error: {str(e)}",
                "result": {}
            }


    async def _initialize_chat(self):
        """Initialize chat, retrieve history and basic info - 優化版"""
        settings = self.containers.cosmos_settings
        
        # ✅ 並行執行所有 I/O 操作
        messages_task = settings.create_GPT_messages(
            self.user_input.session_id, self.user_input.user_input
        )
        hint_task = settings.get_latest_hint(self.user_input.session_id)
        lang_task = settings.get_language_by_websitecode_dev(self.user_input.websitecode)
        
        # ✅ 一次等待所有結果
        results, self.last_hint, self.lang = await asyncio.gather(
            messages_task, hint_task, lang_task
        )
        
        (
            self.his_inputs, self.chat_count, self.user_info,
            self.last_bot_scope, self.last_extract_output
        ) = results
        
        log_json = json.dumps(results, ensure_ascii=False, indent=2)
        logger.info(f"\n[歷史對話]\n{log_json}")

        # ✅ 處理預設值（同步操作，很快）
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())

        logger.info(f"last_hint: {self.last_hint}")

        # ✅ 初始化服務（同步操作）
        self.service_process = ServiceProcess(
            system_code=self.user_input.system_code, container=self.containers
        )
        self.chat_flow = ChatFlow(
            data=self.user_input, last_hint=self.last_hint,
            container=self.containers
        )

        if not self.user_info:
            self.user_info = self.chat_flow.default_user_info
        if (self.user_input.product_line and
                self.last_bot_scope != self.user_input.product_line):
            self.user_info["main_product_category"] = self.user_input.product_line
            self.user_info["first_time"] = True

    async def _process_history(self):
        """Process chat history - 優化版"""
        if len(self.his_inputs) <= 1:
            logger.info(f"his_inputs : {self.his_inputs}")
            async def dummy_follow_up():
                return {"is_follow_up": False}
            
            self.fu_task = asyncio.create_task(dummy_follow_up())
            return
        
        # 準備資料
        self.prev_q = str(self.his_inputs[-2])
        self.prev_a = str(self.last_extract_output.get("answer", ""))
        self.kb_no = str(self.last_extract_output.get("kb", {}).get("kb_no", ""))
        self.content = str(self.containers.KB_mappings.get(
            f"{self.kb_no}_{self.lang}", {}).get("content")
        )

        # ✅ 執行句子分組
        group_task = self.containers.sentence_group_classification
        results_related = await group_task.sentence_group_classification(
            self.his_inputs
        )
        
        # 處理分組結果
        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = (groups[-1].get("statements") or [])
            latest_group_statements = [
                s for s in statements if isinstance(s, str)
            ]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        logger.info(f"last group statements => {self.his_inputs[-1]}")
        logger.info(f"his_inputs : {self.his_inputs}")

        # ✅ 創建 follow-up task（不等待）
        self.fu_task = asyncio.create_task(
            self.chat_flow.is_follow_up(
                prev_question=self.prev_q, prev_answer=self.prev_a,
                prev_answer_refs=self.content, new_question=self.his_inputs[-1]
            )
        )
        

    async def _get_user_and_scope_info(self):
        """Get user info, search info, and determine bot scope - 優化版"""
        
        # ✅ 並行執行所有可以並行的操作
        ui_task = self.chat_flow.get_userInfo(his_inputs=self.his_inputs)
        si_task = self.chat_flow.get_searchInfo(self.his_inputs)
        
        # 並行處理 tech_support_related 判斷
        tech_support_task = None
        if self.last_hint and self.last_hint.get("hintType") == "productline-reask":
            prompt_content = f'''Please determine whether the sentence "{self.his_inputs[-1]}" 
            mentions any technical support-related issues, and reply with "true" or "false" only. 
            Here is an example you can refer to. 
            1. user's question:  it can only be turned on when plugged in. your response: "true" 
            2. user's question:  wearable. your response: "false" 
            3. user's question:  notebook. your response: "false"'''
            prompt = [{"role": "user", "content": prompt_content}]
            tech_support_task = self.chat_flow.container.base_service.GPT41_mini_response(prompt)
        
        # ✅ 使用 gather 並行等待
        results = await asyncio.gather(
            ui_task,
            si_task,
            tech_support_task if tech_support_task else asyncio.sleep(0),
            return_exceptions=True
        )
        
        # 處理結果
        result_user_info = results[0]
        self.user_info_dict = result_user_info[0] if not isinstance(result_user_info, Exception) else {}
        
        search_info_result = results[1]
        tech_support_related = results[2] if tech_support_task else "true"
        
        log_json = json.dumps(self.user_info_dict, ensure_ascii=False, indent=2)
        logger.info(f"\n[使用者資訊]\n{log_json}")
        
        # ✅ 決定 search_info
        if tech_support_related == "false" and self.last_hint:
            self.search_info = self.last_hint.get("searchInfo")
        else:
            self.search_info = search_info_result if not isinstance(search_info_result, Exception) else self.his_inputs[-1]
        
        # ✅ 取得 bot_scope（需要等前面的結果）
        self.bot_scope_chat = self.user_input.product_line or await self.chat_flow.get_bot_scope_chat(
            prev_user_info=self.user_info,
            curr_user_info=self.user_info_dict,
            last_bot_scope=self.last_bot_scope
        )
        
        logger.info(f"\n[Bot Scope 判斷] {self.bot_scope_chat}")

    async def _search_knowledge_base(self):
        """Search knowledge base with product line."""
        response = await self.containers.sd.service_discreminator_with_productline(
            user_question_english=self.search_info,
            site=self.user_input.websitecode,
            specific_kb_mappings=self.containers.specific_kb_mappings,
            productLine=self.bot_scope_chat,
        )
        log_json = json.dumps(response, ensure_ascii=False, indent=2)
        logger.info(
            "[ServiceDiscriminator] discrimination_productline_response: %s",
            log_json
        )
        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    def _process_kb_results(self):
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

    async def _generate_response(self):
        """Generate the final response based on the processed data."""
        if not self.bot_scope_chat:
            self.type = "avatarAskProductLine"
            await self._handle_no_product_line()
        # elif self.is_follow_up and not self.last_extract_output.get("ask_flag"):
        #     await self._handle_follow_up()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            self.type = "avatarTechnicalSupport"
            await self._handle_high_similarity()
        else:
            self.type = "avatarText"
            await self._handle_low_similarity()


    async def _stream_avatar_response(self, content_data=None):
        """Stream avatar response chunks."""
        try:
            # 檢查服務是否支援 streaming
            if hasattr(self.service_process.ts_rag, 'reply_with_faq_gemini_sys_avatar_stream'):
                full_response = ""
                chunk_count = 0
                
                logger.info("[Avatar Streaming] 開始 streaming...")
                
                try:
                    async for chunk in self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar_stream(
                        self.his_inputs[-1], self.lang, content_data
                    ):
                        chunk_count += 1
                        full_response += chunk
                        yield {
                            "status": 200,
                            "message": "OK",
                            "result": {
                                "renderTime": int(time.time()),
                                "render" : [
                                    {
                                        "renderId": self.renderId,
                                        "stream": True,
                                        "type": self.type,
                                        "message": chunk,
                                        "option": [],
                                        "remark": []
                                    }
                                ]
                            }
                        }
                    
                    logger.info(f"[Avatar Streaming] 完成！共收到 {chunk_count} 個 chunks，總長度 {len(full_response)} 字元")
                    
                except Exception as stream_error:
                    logger.error(f"[Avatar Streaming] 迭代中發生錯誤: {stream_error}")
                    import traceback
                    traceback.print_exc()
                    
                    # 如果有部分內容，仍然保存
                    if full_response:
                        logger.info(f"[Avatar Streaming] 保存部分內容: {len(full_response)} 字元")
                
                # 儲存完整的 avatar_response，格式需與原版一致
                # 創建一個簡單的物件來保存 answer
                class AvatarResponse:
                    def __init__(self, answer_text):
                        self.answer = answer_text
                
                self.avatar_response = {
                    'response': AvatarResponse(full_response)
                }
                
                logger.info(f"[Avatar Streaming] avatar_response 已儲存，長度: {len(full_response)} 字元")
                logger.info(f"[Avatar Streaming] 內容預覽: {full_response[:100]}...")
            else:
                # 降級：不支援 streaming，等待完整結果
                if content_data:
                    response = await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                        self.his_inputs[-1], self.lang, content_data
                    )
                    # 處理 reply_gemini_text 的回應格式
                    if isinstance(response, dict) and 'response' in response:
                        answer_text = response['response']
                        self.avatar_response = {
                            'response': type('obj', (object,), {'answer': answer_text})()
                        }
                    else:
                        self.avatar_response = response
                else:
                    self.avatar_response = await self.avatar_process
                
                # 取得 answer 文字
                answer_text = ""
                if hasattr(self.avatar_response, 'get') and 'response' in self.avatar_response:
                    if hasattr(self.avatar_response['response'], 'answer'):
                        answer_text = self.avatar_response['response'].answer
                    else:
                        answer_text = str(self.avatar_response['response'])
                elif isinstance(self.avatar_response, dict) and 'response' in self.avatar_response:
                    answer_text = self.avatar_response['response']
                else:
                    answer_text = str(self.avatar_response)
                
                yield {
                    "status": 200,
                    "message": "OK",
                    "result": {
                        "type": "avatar_complete",
                        "content": answer_text,
                        "is_final": True
                    }
                }
        except Exception as e:
            logger.error(f"Avatar streaming error: {e}")
            yield {
                "status": 500,
                "message": f"error: {str(e)}",
                "result": {}
            }

    async def _handle_no_product_line_stream(self):
        """Handle no product line case with streaming."""
        logger.info("\n[無產品線] 進行產品線追問")
        
        # Stream avatar response
        async for event in self._stream_avatar_response():
            yield event
        
        # 執行產品線追問
        reask_task = self.service_process.technical_support_productline_reask
        ask_response, rag_response = await reask_task(
            user_input=self.user_input.user_input,
            faqs_wo_pl=self.faqs_wo_pl,
            site=self.user_input.websitecode,
            lang=self.lang,
            system_code=self.user_input.system_code,
        )
        relative_questions = rag_response.get("relative_questions", [])
        
        await self.containers.cosmos_settings.insert_hint_data(
            chatflow_data=self.chat_flow.data,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask",
        )
        
        self.response_data = {
            "status": 200, 
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": ask_response["ask_content"],
                "ask_flag": ask_response["ask_flag"],
                "hint_candidates": relative_questions,
                "kb": {}
            }
        }

        # 最終完整結果
        self.result = {
            "renderTime": int(time.time()),
            "render":[
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": self.avatar_response['response'].answer,
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
        
        yield {
            "status": 200,
            "message": "OK",
            "result": self.result
        }
        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": self.result
        }

    async def _handle_high_similarity_stream(self):
        """Handle high similarity case with streaming."""
        logger.info(
            f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應"
        )
        
        rag_response = await self.service_process.technical_support_hint_create(
            self.top4_kb_list, self.top1_kb, self.top1_kb_sim, self.lang,
            self.search_info, self.his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode, config=self.containers.cfg
        )
        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})
        
        # Stream avatar response with content
        async for event in self._stream_avatar_response(content):
            yield event

        self.response_data = {
            "status": 200, 
            "type": "answer", 
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": rag_response.get("relative_questions", []),
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(info.get("top1_similarity", 0.0) or 0.0),
                    "source": info.get("response_source", ""),
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0)
                }
            },
        }

        # 最終完整結果
        self.result = {
            "renderTime": int(time.time()),
            "render":[
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": self.avatar_response['response'].answer,
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
        yield {
            "status": 200,
            "message": "OK",
            "result": self.result
        }
        self. final_result = {
            "status": 200,
            "message": "OK",
            "result": self.result
        }

    async def _handle_low_similarity_stream(self):
        """Handle low similarity case with streaming."""
        logger.info(f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")
        
        # Stream avatar response
        async for event in self._stream_avatar_response():
            yield event

        self.response_data = {
            "status": 200, 
            "type": "handoff", 
            "message": "相似度低，建議轉人工",
            "output": {
                "answer": "", 
                "ask_flag": False, 
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""), 
                    "title": str(self.containers.KB_mappings.get(
                        f"{self.top1_kb}_{self.lang}", {}).get("title", "")
                    ),
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "", 
                    "exec_time": 0.0
                }
            },
        }

        # 第一部分：回傳 avatarText
        avatarText_result = {
            "renderTime": int(time.time()),
            "render":[
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarText",
                    "message": self.avatar_response['response'].answer,
                    "remark": [],
                    "option": []
                }
            ]
        }

        yield {
            "status": 200,
            "message": "OK",
            "result": [avatarText_result]
        }
        
        # 第二部分：回傳 avatarAsk
        avatarAsk_result = {
            "renderTime": int(time.time()),
            "render":[
                {
                    "renderId": self.renderId,
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
        yield {
            "status": 200,
            "message": "OK",
            "result": [avatarAsk_result]
        }
        
        # 保存完整的結果供後續使用
        self.result = [avatarText_result, avatarAsk_result]
        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": self.result
        }


    async def _handle_no_product_line(self):
        logger.info("\n[無產品線] 進行產品線追問")
        reask_result_task = asyncio.create_task(self.service_process.technical_support_productline_reask(
            user_input=self.user_input.user_input,
            faqs_wo_pl=self.faqs_wo_pl,
            site=self.user_input.websitecode,
            lang=self.lang,
            system_code=self.user_input.system_code,
        ))
        self.avatar_response, (ask_response, rag_response) = await asyncio.gather(
            self.avatar_process, reask_result_task
        )
        relative_questions = rag_response.get("relative_questions", [])
        await self.containers.cosmos_settings.insert_hint_data(
            chatflow_data=self.chat_flow.data,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask",
        )
        self.response_data = {
            "status": 200, 
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": ask_response["ask_content"],
                "ask_flag": ask_response["ask_flag"],
                "hint_candidates": relative_questions,
                "kb": {}
            }
        }
        self.final_result = {
            "status" : 200,
            "message" : "OK",
            "result" : [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": self.avatar_response['response'],
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

    async def _handle_follow_up(self):
        logger.info(f"\n[延續問題追問] 使用上次回覆內容")
        rag_response = await self.service_process.technical_support_hint_follow_up(
            self.top4_kb_list, 
            self.top1_kb, 
            self.top1_kb_sim, 
            self.lang,
            self.search_info, 
            self.his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode, 
            last_question=self.prev_q,
            last_answer=self.prev_a, 
            last_kb=self.kb_no,
        )
        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})
        self.response_data = {
            "status": 200, 
            "type": "follow_up_question",
            "message": "Follow-up question, use previous answer",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": rag_response.get("relative_questions", []),
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(info.get("top1_similarity", 0.0) or 0.0),
                    "source": info.get("response_source", ""),
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0)
                }
            },
            "avatar_output": {
                "renderId": "",
                "stream": False,
                "type": "avatarTechnicalSupport",
                "message": self.avatar_response['response'].answer,
                "remark": [],
                "option": [
                    {
                        "type": "",
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
        }

    async def _handle_high_similarity(self):
        logger.info(
            f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應"
        )
        rag_response = await self.service_process.technical_support_hint_create(
            self.top4_kb_list, self.top1_kb, self.top1_kb_sim, self.lang,
            self.search_info, self.his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode, config=self.containers.cfg
        )
        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})
        self.avatar_response = await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(self.his_inputs[-1], self.lang, content)
        self.response_data = {
            "status": 200, 
            "type": "answer", 
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": rag_response.get("relative_questions", []),
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(info.get("top1_similarity", 0.0) or 0.0),
                    "source": info.get("response_source", ""),
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0)
                }
            },
        }
        self.final_result = {
            "status" : 200,
            "message" : "OK",
            "result" : [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": self.avatar_response['response'].answer,
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

    async def _handle_low_similarity(self):
        logger.info(f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")
        self.avatar_response = await self.avatar_process
        self.response_data = {
            "status": 200, 
            "type": "handoff", 
            "message": "相似度低，建議轉人工",
            "output": {
                "answer": "", 
                "ask_flag": False, 
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""), 
                    "title": str(self.containers.KB_mappings.get(
                        f"{self.top1_kb}_{self.lang}", {}).get("title", "")
                    ),
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "", 
                    "exec_time": 0.0
                }
            },
        }
        self.final_result = {
            "status" : 200,
            "message" : "OK",
            "result" : [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarText",
                    "message": self.avatar_response['response'].answer,
                    "remark": [],
                    "option": []
                },
                {
                    "renderId": self.renderId,
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

    async def _log_and_save_results(self):
        """Log and save the final results to Cosmos DB."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        logger.info(f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n")
        cosmos_data = {
            "id": f"{self.user_input.cus_id}-{self.user_input.session_id}-{self.user_input.chat_id}",
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
                "last_info": {
                    "prev_q": self.prev_q,
                    "prev_a": self.prev_a,
                    "kb_no": self.kb_no,
                },
            },
            "final_result" : self.final_result,
            "extract": self.response_data,
            "total_time": exec_time
        }
        asyncio.create_task(self.containers.cosmos_settings.insert_data(cosmos_data))
        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        logger.info(f"\n[Cosmos DB] 寫入資料: {log_json}\n")

        return cosmos_data


async def tech_agent_api(containers, user_input: TechAgentInput):
    processor = TechAgentProcessor(containers, user_input)
    return await processor.process()


