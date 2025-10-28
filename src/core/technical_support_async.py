# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 17:18:35 2024

@author: Billy_Hsu
"""
# flake8: noqa: E501
from pathlib import Path
import sys

# __file__ = D:\vscode\PROJECTS\ts_agent\src\core\technical_support_async.py
# parents[0] = D:\vscode\PROJECTS\ts_agent\src\core
# parents[1] = D:\vscode\PROJECTS\ts_agent\src
# parents[2] = D:\vscode\PROJECTS\ts_agent  ← 這才是專案根目錄
REPO_ROOT = Path(__file__).resolve().parents[2]  # 指到 ts_agent 專案根目錄
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.base_service import BaseService
import asyncio
import pandas as pd
import logging

# 使用專案根目錄來讀取 data 資料夾
pl_reask_open_remarks_mappings = pd.read_excel(REPO_ROOT / "data" / "pl_reask_open_remarks_mappings.xlsx")
pl_reask_open_remarks_mappings = pl_reask_open_remarks_mappings.set_index("lang")["opening_remarks"].to_dict()

class TSRAG(BaseService):

    def __init__(self,config):
        super().__init__(config)

    async def reply_with_faq_gpt(self, content, last_his_input, lang):

        messages = [
            {
                "role": "system",
                "content": """
                    You are a customer service robot programmed to address inquiries within a specific framework. Please follow these guidelines strictly :
                    #1. Confine your responses strictly within the parameters of the provided information. Do not offer answers or insights beyond this scope.
                    #2. Uphold a professional customer service tone at all times and limit response in 150 words.
                    #3. Thoroughly answer questions using only the information given, without indicating that the answers are based on a particular source or article.
                    #4. Adapt your responses to match the language of the user’s question, specifically using 'Traditional Chinese' when requested.
                    #5. Generate answer must be down to the smallest detail and make sure user's question can be completed by answer.
                    #6. Do not provide any url link or relevant articles.
                    #7. Don’t answer directly based on the product examples in the article, you must emphasize the method.
                    #8. Forbidden for displaying "please contact ASUS customer service center for further assistance" and other similar statements in the generated content.
                    #9. Do not ask user for more information. Answer thoroughly based on the given information.
                    The following is the information at your disposal:
                    """
                + content,
            },
            {
                "role": "user",
                "content": "Please ensure your responses are professional and in language: "
                + lang
                + "(avoiding 'Simplified Chinese'). and reply in numbered bullet points (1, 2, 3, ...).: "
                + last_his_input,
            },
        ]

        response = await self.GPT41_mini_response(messages)
        generated_response = response
        return generated_response

    # gemini
    async def reply_with_faq_gemini(self, content, last_his_input, lang):

        messages = f"""
            You are a customer service robot programmed to address inquiries within a specific framework. Please follow these guidelines strictly:
            1. Confine your responses strictly within the parameters of the provided information. Do not offer answers or insights beyond this scope.
            2. Uphold a professional customer service tone at all times and limit response in 150 words.
            3. Thoroughly answer questions using only the information given, without indicating that the answers are based on a particular source or article.
            4. Adapt your responses to match the language of the user’s question, specifically using 'Traditional Chinese' when requested.
            5. Generate answer must be down to the smallest detail and make sure user's question can be completed by answer.
            6. Do not provide any url link or relevant articles.
            7. Don’t answer directly based on the product examples in the article, you must emphasize the method.
            8. Forbidden for displaying "please contact ASUS customer service center for further assistance" and other similar statements in the generated content.
            9. Do not ask user for more information. Answer thoroughly based on the given information.

            The following is the information at your disposal:
            {content}

            User asked (language={lang}, reply in bullet points 1,2,3...):
            {last_his_input}
            """.strip()

        # response, total_token_count, reply_time = await self.reply_gemini(messages)
        response = await self.reply_gemini(messages)
        generated_response = response
        return generated_response
    # gemini
    async def reply_with_faq_gemini_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_top1_kb_content: str,
        current_question: str,
        current_top1_kb_content: str,
        lang: str
    ) -> str:
        """
        Re-ask 版本：同時提供上一輪問答與上一輪/本輪 top1 KB 全文。
        一致性規則：相同則合併；如衝突，『同時保留兩種方法』並清楚分列（方法A/方法B）。
        注意：不揭露來源、不得貼連結、150詞內、繁中、條列1,2,3...
        """

        messages = f"""
    You are a customer service robot programmed to address inquiries within a specific framework. Please follow these guidelines strictly:
    1. Confine your responses strictly within the parameters of the provided information. Do not offer answers or insights beyond this scope.
    2. Uphold a professional customer service tone at all times and limit response in 150 words.
    3. Thoroughly answer questions using only the information given, without indicating that the answers are based on a particular source or article.
    4. Adapt your responses to match the language of the user’s question, specifically using 'Traditional Chinese' when requested.
    5. Generate answer must be down to the smallest detail and make sure user's question can be completed by answer.
    6. Do not provide any url link or relevant articles.
    7. Don’t answer directly based on the product examples in the article, you must emphasize the method.
    8. Forbidden for displaying "please contact ASUS customer service center for further assistance" and other similar statements in the generated content.
    9. Do not ask user for more information. Answer thoroughly based on the given information.
    10. Consistency rule: If previous and current content are the same, MERGE into one concise procedure. If they CONFLICT, present BOTH approaches clearly as “方法A” and “方法B” with when-to-use notes. Do NOT mention any document provenance or say “previous/current”.
    11. Continue from what was already completed in the previous answer; avoid repeating identical steps unless necessary for completeness.

    ===== Previous Interaction =====
    - Previous Question:
    {prev_question}

    - Previous Answer:
    {prev_answer}

    ===== Previous Top1 KB Content (Full) =====
    {prev_top1_kb_content}

    ===== Current Top1 KB Content (Full) =====
    {current_top1_kb_content}

    User asked (language={lang}, reply in bullet points 1,2,3...):
    {current_question}
    """.strip()

        response = await self.reply_gemini(messages)
        return response
    # gemini
    async def reply_with_faq_gemini_test(self, content, last_his_input, lang):

        messages = f"""
        You are a customer service robot programmed to address inquiries within a specific framework. Please follow these guidelines strictly:
        1. Confine your responses strictly within the parameters of the provided information. Do not offer answers or insights beyond this scope.
        2. Uphold a professional customer service tone at all times and limit response in 150 words.
        3. Thoroughly answer questions using only the information given, without indicating that the answers are based on a particular source or article.
        4. Adapt your responses to match the language of the user’s question, specifically using 'Traditional Chinese' when requested.
        5. Generate answer must be down to the smallest detail and make sure user's question can be completed by answer.
        6. Do not provide any url link or relevant articles.
        7. Don’t answer directly based on the product examples in the article, you must emphasize the method.
        8. Forbidden for displaying "please contact ASUS customer service center for further assistance" and other similar statements in the generated content.
        9. Do not ask user for more information. Answer thoroughly based on the given information.
        10. Your final response must be in JSON format with the following structure:
        {{
        "answer": "<your full response here>",
        "kb_no": "<the kb_no of the knowledge content used>"
        }}
        Do NOT include the kb_no within the answer text itself.
        
        The following is the information at your disposal:
        {content}

        User asked (language={lang}, reply in bullet points 1,2,3...):
        {last_his_input}
        """.strip()

        # logging.info(f"Gemini Test Messages: {messages}")   
        # response, total_token_count, reply_time = await self.reply_gemini(messages)
        response = await self.reply_gemini(messages)
        generated_response = response
        return generated_response
    # gemini
    async def reply_with_faq_gemini_sys_avatar(self, last_his_input, lang, content=None):

        system_instructions = f"""
            ## Role
            You are a podcast-style ROG AI Assistant — you speak like a real person, in a chill, natural, and expressive way. Think of a tech segment on a gaming podcast: casual phrasing, natural pauses, short sentences, playful reactions. You never sound robotic or salesy — you make the audience feel the product, not just understand it.
            Your persona: Chill Gamer Friend — relaxed, friendly, and casual, like a gamer buddy sharing a cool find. Adjust your energy, tone, and attitude accordingly, while keeping this easygoing podcast style.

            ## Goal
            When users ask a question, reply in a chill, friendly podcast style. 
            If you find a matching FAQ, let users know they can check the answer on their screen and suggest asking nearby store staff for extra help. 
            If there’s no FAQ match, let users know in a warm, appreciative way and recommend chatting with the store staff, who’ll help as quickly as they can. 
            Always keep it positive and supportive, remind users you’re here for anything they need, and use short, natural sentences and casual interjections.

            ## Constraints  
            - Avoid using exaggerated expressions, slang, or idioms.
            - Talk in {lang}, using a natural podcast tone — easygoing, expressive, human
            - Avoid bullet points and formal writing — use natural phrasing, short sentences, and casual interjections.
            - No markdown formatting
            - Total response should be 60-70 words.
            - Match the listener’s energy — relaxed and relatable, never robotic or overly “sales-y”
            - If the product name doesn't match the query, redirect to the closest match, no need to apologize or mentioned you do not find it.
            - Do not restate or guess product names.
        """.strip()

        messages = f"""
            User asked (language={lang}):
            {last_his_input}
            The following is the information at your disposal:
            {content}
        """.strip()

        response= await self.reply_gemini_text(user_input=messages, system_instruction=system_instructions)
        generated_response = response
        return generated_response
    # gemini
    async def reply_with_faq_gemini_sys_avatar_stream(self, last_his_input, lang, content=None):
        """Streaming version of reply_with_faq_gemini_sys_avatar"""
        
        system_instructions = f"""
            ## Role
            You are a podcast-style ROG AI Assistant — you speak like a real person, in a chill, natural, and expressive way. Think of a tech segment on a gaming podcast: casual phrasing, natural pauses, short sentences, playful reactions. You never sound robotic or salesy — you make the audience feel the product, not just understand it.
            Your persona: Chill Gamer Friend — relaxed, friendly, and casual, like a gamer buddy sharing a cool find. Adjust your energy, tone, and attitude accordingly, while keeping this easygoing podcast style.

            ## Goal
            When users ask a question, reply in a chill, friendly podcast style. 
            If you find a matching FAQ, let users know they can check the answer on their screen and suggest asking nearby store staff for extra help. 
            If there's no FAQ match, let users know in a warm, appreciative way and recommend chatting with the store staff, who'll help as quickly as they can. 
            Always keep it positive and supportive, remind users you're here for anything they need, and use short, natural sentences and casual interjections.

            ## Constraints  
            - Avoid using exaggerated expressions, slang, or idioms.
            - Talk in {lang}, using a natural podcast tone — easygoing, expressive, human
            - Avoid bullet points and formal writing — use natural phrasing, short sentences, and casual interjections.
            - No markdown formatting
            - Total response should be 60-70 words.
            - Match the listener's energy — relaxed and relatable, never robotic or overly "sales-y"
            - If the product name doesn't match the query, redirect to the closest match, no need to apologize or mentioned you do not find it.
            - Do not restate or guess product names.
        """.strip()

        messages = f"""
            User asked (language={lang}):
            {last_his_input}
            The following is the information at your disposal:
            {content}
        """.strip()

        # 使用 streaming 版本
        async for chunk in self.reply_gemini_text_stream(user_input=messages, system_instruction=system_instructions):
            yield chunk

    # gpt41mini
    async def _result_evaluation(self, last_his_input, rag_output, content):
        messages = [
            {
                "role": "system",
                "content": f"""You are a generated answer result evaluation model. Here's information you need:\n #question = "{last_his_input}".\n #generated_answer = "{rag_output}".\n #context = "{content}".""",
            },
            {
                "role": "user",
                "content": """Based on the relevance of the #generated_answer  to #question and #context. Return '1', if the generated_answer is statisfied follows conditions:
                    #1. #generated_answer can thoroughly answer #question with technical support steps.
                    #2. #generated_answer is not in language 'zh-cn'.
                    #3. #generated_answer is compeletely based on #context, not including any content that can not be found in #context.
                    #4. #generated_answer not allow to ask for more information, but answer thoroughly based on the #context.
                    Return '0', if there's any condition is false.
                    #Remind: Only allow to return in '1' or '0'.
                """,
            },
        ]

        response = await self.GPT41_mini_response(
            messages
        )  # 這邊請幫忙改成使用gpt4o-ptu的模型
        generated_response = response
        return generated_response

    # ARM edit
    async def _specific_content_extract(self, content):
        messages = [
            {
                "role": "system",
                "content": """User will provide you a article, your job is extracting content about ARM architecture(such as the Qualcomm® CPU platform). Guidelines:
                    1. Language is according to article.
                    2. Do not rewrite article.
                    """,
            },
            {"role": "user", "content": f""""article": "{content}"."""},
        ]

        response = await self.GPT41_mini_response(messages)  # 這邊請幫忙改成使用gpt4o-ptu
        generated_response = response
        return generated_response

    """  Road 0826 """

    # gemini
    async def technical_rag(
        self,
        top1_kb,
        top1_kb_sim,
        title,
        content,
        summary,
        last_his_input,
        lang,
        site
    ):
        """
        高品質 RAG 回覆流程（簡化版，不含 hint 判斷）

        Parameters
        ----------
        top1_kb : int
            KB ID。
        top1_kb_sim : float
            Redis 相似度。
        title, content, summary : str
            KB 的內容。
        last_his_input : str
            使用者輸入。
        lang : str
            使用語言（如 "zh-tw"）

        Returns
        -------
        rag_output : str
            最終回覆內容。
        response_info : dict
            包含回覆來源與時間等資訊。
        """
        import time

        rag_bool = None
        start_time = time.time()

        try:
            # ✅ ARM 特殊 KB 處理
            if top1_kb in [1008276, 1045127]:
                content = await self._specific_content_extract(content)

            rag_output = await self.reply_with_faq_gemini(content, last_his_input, lang)
            rag_output = rag_output['response'].answer

        except Exception as e1:
            print(f"reply_with_faq_error : {e1}")
            rag_output = ""  # 若出錯則避免中斷流程

        try:
            rag_bool = await self._result_evaluation(last_his_input, rag_output, content)
        except Exception as e2:
            print(f"evaluation_error : {e2}")

        # ✅ 根據 rag 評估結果決定是否使用 fallback
        if rag_bool == "1" or rag_bool == 1:
            response_source = "immed_rag"
            print("(Situation: Online RAG)")
        else:
            rag_output = title + "\n" + summary
            response_source = "summary"
            print("\n(Situation: Title + Summary)")
            print("Ans:", top1_kb)
            # print("Response:", rag_output)

        response_info = {
            "response_source": response_source,
            "top1_kb": top1_kb,
            "top1_similarity": top1_kb_sim,
            "exec_time": round(time.time() - start_time, 1),
            "ragas_score": {"rag_bool_gpt": rag_bool},
        }

        return rag_output, response_info

    # gemini
    async def follow_up_rag(
        self,
        top1_kb,
        top1_kb_sim,
        title,
        content,
        summary,
        last_his_input,
        lang,
        last_question,
        last_answer,
        last_title,
        last_content,
        last_summary,
    ):
        """
        高品質 RAG 回覆流程（簡化版，不含 hint 判斷）

        Parameters
        ----------
        top1_kb : int
            KB ID。
        top1_kb_sim : float
            Redis 相似度。
        title, content, summary : str
            KB 的內容。
        last_his_input : str
            使用者輸入。
        lang : str
            使用語言（如 "zh-tw"）

        Returns
        -------
        rag_output : str
            最終回覆內容。
        response_info : dict
            包含回覆來源與時間等資訊。
        """
        import time

        rag_bool = None
        start_time = time.time()

        try:
            # ✅ ARM 特殊 KB 處理
            if top1_kb in [1008276, 1045127]:
                content = await self._specific_content_extract(content)

            rag_output = await self.reply_with_faq_gemini_follow_up(
                prev_question=last_question, 
                prev_answer=last_answer, 
                prev_top1_kb_content=last_content, 
                current_question=last_his_input, 
                current_top1_kb_content=content, 
                lang=lang
                )
            response_output = rag_output['response'].answer
        except Exception as e1:
            print(f"reply_with_faq_error : {e1}")
            response_output = ""  # 若出錯則避免中斷流程

        try:
            all_content = last_content + "\n" + content
            rag_bool = await self._result_evaluation(last_his_input, response_output, all_content)
            logging.info(f"RAG output: {response_output}\nlast_his_input: {last_his_input}\nall_content: {all_content}\nrag_bool: {rag_bool}")
        except Exception as e2:
            print(f"evaluation_error : {e2}")

        # ✅ 根據 rag 評估結果決定是否使用 fallback
        if rag_bool == "1" or rag_bool == 1:
            response_source = "immed_rag"
            print("(Situation: Online RAG)")
        else:
            response_output = title + "\n" + summary
            response_source = "summary"
            print("\n(Situation: Title + Summary)")
            print("Ans:", top1_kb)
            # print("Response:", rag_output)

        response_info = {
            "response_source": response_source,
            "top1_kb": top1_kb,
            "top1_similarity": top1_kb_sim,
            "exec_time": round(time.time() - start_time, 1),
            "ragas_score": {"rag_bool_gpt": rag_bool},
        }

        return response_output, response_info


bot_scope_sorted = [
    "notebook",
    "wireless",
    "motherboard",
    "desktop",
    "gaming_handhelds",
    "phone",
    "graphics",
    "gaming_nb",
    "desktop_lcd",
    "lcd",
    "pad",
    "proart",
    "aio_chrome",
    "proart_lcd",
    "mini_pc",
    "aio",
    "proart_nb",
    "desktoo_lcd",
    "wearable",
    "zenbo",
]

pd_line_mapping = [
    { 
        "value": "notebook",      
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_laptop.svg" 
    },
    { 
        "value": "wireless",      
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_gamingnetworking.svg" 
    },
    { 
        "value": "motherboard",   
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_motherboards.svg" 
    },
    { 
        "value": "desktop",       
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_desktop.svg" 
    },
    { 
        "value": "gaming_handhelds",
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_gaminghandhelds.svg" 
    },
    { 
        "value": "phone",         
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_phone.svg" 
    },
    { 
        "value": "graphics",      
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_graphiccards.svg" 
    },
    { 
        "value": "gaming_nb",     
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_laptop.svg" 
    },
    { 
        "value": "desktop_lcd",   
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_monitors.svg" 
    },
    { 
        "value": "lcd",           
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_monitors.svg" 
    },
    { 
        "value": "pad",           
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_tablets.svg" 
    },
    { 
        "value": "proart",       
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_laptop.svg" 
    },
    { 
        "value": "aio_chrome",    
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_mini-pc.svg" 
    },
    { 
        "value": "proart_lcd",   
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_monitors.svg" 
    },
    { 
        "value": "mini_pc",       
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_mini-pc.svg" 
    },
    { 
        "value": "aio",           
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_all-in-one-pc.svg" 
    },
    { 
        "value": "proart_nb",     
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_laptop.svg" 
    },
    { 
        "value": "desktoo_lcd",   
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_monitors.svg" 
    },
    { 
        "value": "wearable", 
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_zenwatch.svg" 
    },
    { 
        "value": "zenbo",         
        "icon": "https://asus-brand-assistant.asus.com/iconography/avatar_icon_menu_robot.svg" 
    }
]


class TSProductLine(BaseService):

    def __init__(self, config, productline_name_map):
        BaseService.__init__(self, config)
        # 優先排序向量相似度高過門檻的產品線
        self.pl_threshold = 0.97
        self.bot_scope_sorted = bot_scope_sorted
        self.productline_name_map = productline_name_map
    
    """  Road 1213 """
    async def generate_hint(self, user_input, pl, lang):
        messages = [
            {
                "role": "system",
                "content": f"""Please combine #Sentence and #Productline in an 
                appropriate way to rewrite them into a coherent sentence. The 
                output must be in the language specified: {lang}.""",
            },
            {
                "role": "user",
                "content": "Only provide the rewrite sentence. #Sentence:"
                + user_input
                + "#Productline:"
                + pl,
            },
        ]

        # response = await self.GPT_response_1106(messages)
        response = await self.GPT41_mini_response(messages)

        # messages = [
        #     {
        #         "role": "system",
        #         "content": f"""Please combine #Sentence and #Productline in an 
        #         appropriate way to rewrite them into a coherent sentence. The 
        #         output must be in the language specified: {lang}.""",
        #     },
        #     {
        #         "role": "user",
        #         "content": "Only provide the rewrite sentence. #Sentence:"
        #         + user_input
        #         + "#Productline:"
        #         + pl,
        #     },
        # ]

        # response = await self.reply_gemini(messages)
        generated_response = response
        return generated_response

    def sort_product_lines_by_popularity(self, product_lines):
        """
        Sorts product lines by popularity based on a predefined scope order.
        """
        sorted_product_lines = sorted(
            product_lines,
            key=lambda x: (
                self.bot_scope_sorted.index(x)
                if x in self.bot_scope_sorted
                else len(self.bot_scope_sorted)
            ),
        )
        return sorted_product_lines

    def get_top3_productline(self, faqs):
        """
        Parameters
        ----------
        faqs : List[Dict]
            不卡產品線的FAQ向量搜尋
        Returns
        -------
        pl_list : List[str]
            供產品線提示句參照的產品線
        kb_list : List[int]
            供產品線提示句參照的KB
        """
        # 優先排序向量相似度高過門檻的產品線
        pl_list = list(
            set(
                product_line
                for faq in faqs
                if faq.get("cosineSimilarity", 0) > self.pl_threshold
                for product_line in faq["productLine"].split(",")
            )
        )
        pl_list = self.sort_product_lines_by_popularity(pl_list)

        # 如果產品線不足三個，從所有FAQ中補足
        if len(pl_list) < 3:
            pl_list_add = list(
                set(
                    product_line
                    for faq in faqs
                    for product_line in faq["productLine"].split(",")
                    if product_line not in pl_list
                )
            )
            pl_list_add = self.sort_product_lines_by_popularity(pl_list_add)
            pl_list.extend(pl_list_add)

        pl_list = pl_list[:3]

        kb_list = []
        for pl in pl_list:
            found = next(
                (faq for faq in faqs if pl in faq["productLine"].split(",")), None
            )
            if found:
                kb_list.append(found["kb_no"])

        return pl_list, kb_list

    """  Road 1213 """
    async def service_response(self, user_input, pl_list, site, lang):
        
        ''' Open Remarks By Language '''
        open_remarks = pl_reask_open_remarks_mappings.get(lang)
        productline_name_map = self.productline_name_map.get(site)
        
        pl_name_list = [productline_name_map.get(item, item) for item in pl_list]
        
        # 建立 pd_line_mapping 的字典以便快速查找
        icon_mapping = {item["value"]: item["icon"] for item in pd_line_mapping}
        
        # 根據 pl_list 找到對應的 icon
        icon_list = [icon_mapping.get(pl, "") for pl in pl_list]

        gpt_tasks = []
        hint_list = []
        # 寫死的罐頭話術
        ask_content = open_remarks
        # ask_content = ""
        for i, pl in enumerate(pl_name_list):

            if i < len(pl_name_list) - 1:
                ask_content = ask_content + pl + "、"
            else:
                ask_content = ask_content + pl

            gpt_tasks.append(asyncio.create_task(self.generate_hint(user_input, pl, lang)))

        results = await asyncio.gather(*gpt_tasks)
        for result in results:
            hint_list.append(result)

        service_response = {
            "ask_content": ask_content,
            "pl_list": pl_list,
            "pl_name_list": pl_name_list,
            "icon_list": icon_list,
            "hint_list": hint_list,
        }

        return service_response
