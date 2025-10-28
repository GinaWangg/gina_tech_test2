# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 17:40:36 2024

@author: Billy_Hsu
"""
# flake8: noqa: E501
import base64
import time
import asyncio
from openai import AsyncAzureOpenAI
import json
import re
from google import genai
from google.genai.types import Content, Part, GenerateContentConfig
from google.oauth2 import service_account
from pydantic import BaseModel

class response_struct(BaseModel):
    kb_no: str
    answer: str

class BaseService:
    def __init__(self, config=None):
        # Use provided config or fallback to environment variables
        if config is None:
            config = config

        self.config = config

        self.model_gpt41_mini = config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_MODEL")
        self.openai_client_gpt41_mini = AsyncAzureOpenAI(
            azure_endpoint=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_AZURE_ENDPOINT"),
            api_key=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_API_KEY"),
            api_version=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_API_VERSION"),
            timeout=30,
        )
      
        self.system_messages = [
            {
                "role": "system",
                "content": """
The assistant acts as an ASUS customer service specialist.Your task is to assist users in know thier repair status.
Please gather the following parameters for function calls: ["sn" (product serial number), "rmano" (repair order number)].

Guidelines for the Assistant:
** Do not make assumptions about the function parameters. If a user's request is not clear, especially regarding the sn or rmano, seek further clarification.
** If the user has not specified a sn or rmano, please ask them to provide this information.
** Respond in a clear and concise manner.

You Must follow::
** Translate any function arguments into English before use.
** Please Answer in English.
** You can not answer anything not related to ASUS customer service, you can not deal with personally identifiable information data.
""",
            }
        ]

        # GCP Gemini (Vertex AI)
        # CREDS_PATH = config_path("TECH_GEMINI_CREDENTIALS_JSON")
        # self.gemini_credentials = service_account.Credentials.from_service_account_file(
        #     CREDS_PATH,
        #     scopes=["https://www.googleapis.com/auth/cloud-platform"],
        # )
        SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
        info = json.loads(base64.b64decode(self.config.get("TECH_GEMINI_CREDENTIALS")))
        self.gemini_credentials = service_account.Credentials.from_service_account_info(info).with_scopes(SCOPES)

        # 建立 GenAI client
        self.client = genai.Client(vertexai=True, project=self.gemini_credentials.project_id, location=config.get("TECH_GEMINI_LOCATION"), credentials=self.gemini_credentials)
        self.model_name = config.get("TECH_GEMINI_MODEL_NAME")
    

    # 現在用這個gemini
    async def reply_gemini(self, user_input: str, max_retries: int = 3, retry_delay: float = 2.0):
        def _is_blank(x):
            return x is None or (isinstance(x, str) and x.strip() == "")

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[Content(role="user", parts=[Part(text=user_input)])],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": list[response_struct],
                    },
                )

                resp0 = response.parsed[0]
                kb_no = resp0.get("kb_no") if isinstance(resp0, dict) else getattr(resp0, "kb_no", None)
                answer = resp0.get("answer") if isinstance(resp0, dict) else getattr(resp0, "answer", None)

                # 內容驗證：kb_no 或 answer 為空 -> 視為失敗，觸發重試
                if _is_blank(kb_no) or _is_blank(answer):
                    raise ValueError("kb_no or answer is blank")

                return {
                    "response": resp0,
                    "total_token_count": response.usage_metadata.total_token_count if response.usage_metadata else 0,
                    "reply_time": round(time.time() - start_time, 2),
                }

            except Exception as e:
                print(f"[Gemini Error] 第 {attempt} 次嘗試失敗：{e}")
                if attempt == max_retries:
                    print("[Gemini Error] 已達最大重試次數，放棄重試。")
                    return {
                        "response": {
                            "answer": "⚠️ Gemini 無法回應，請稍後再試。",
                            "kb_no": ""
                        },
                        "total_token_count": 0,
                        "reply_time": 0.0,
                    }
                await asyncio.sleep(retry_delay)

    async def reply_gemini_sys(
        self, user_input: str, system_instruction: str,
        max_retries: int = 3, retry_delay: float = 2.0
    ):
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        Content(role="user", parts=[Part(text=user_input)])
                    ],
                    config=GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=list[response_struct],
                    ),
                )
                
                resp0 = response.parsed[0]
                kb_no = (
                    resp0.get("kb_no") if isinstance(resp0, dict) 
                    else getattr(resp0, "kb_no", None)
                )
                answer = (
                    resp0.get("answer") if isinstance(resp0, dict) 
                    else getattr(resp0, "answer", None)
                )
                
                return {
                    "response": resp0,
                    "total_token_count": (
                        response.usage_metadata.total_token_count 
                        if response.usage_metadata else 0
                    ),
                    "reply_time": round(time.time() - start_time, 2),
                }
            except Exception as e:
                print(f"[Gemini Error] 第 {attempt} 次嘗試失敗：{e}")
                if attempt == max_retries:
                    print("[Gemini Error] 已達最大重試次數，放棄重試。")
                    return {
                        "response": {
                            "answer": "⚠️ Gemini 無法回應，請稍後再試。",
                            "kb_no": ""
                        },
                        "total_token_count": 0,
                        "reply_time": 0.0,
                    }
                await asyncio.sleep(retry_delay)

    async def reply_gemini_text_stream(
        self, user_input: str, system_instruction: str,
        max_retries: int = 3, retry_delay: float = 2.0,
        char_by_char: bool = True  # 新增參數：是否逐字輸出
    ):
        """Streaming version for text generation (not structured JSON)"""
        for attempt in range(1, max_retries + 1):
            try:
                # Gemini SDK 的 generate_content_stream 是同步的 iterator
                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[Content(role="user", parts=[Part(text=user_input)])],
                    config=GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                )

                # 使用同步的 for loop，但包在 async function 中
                chunk_count = 0
                for chunk in response:
                    chunk_count += 1
                    text = None
                    
                    # 嘗試多種方式取得 text
                    if hasattr(chunk, 'text') and chunk.text:
                        text = chunk.text
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        try:
                            text = chunk.candidates[0].content.parts[0].text
                        except (IndexError, AttributeError):
                            pass
                    
                    if text:
                        if char_by_char:
                            # 逐字 yield
                            for char in text:
                                yield char
                        else:
                            # 直接 yield chunk
                            yield text

                print(f"[Gemini Stream] 成功完成，共收到 {chunk_count} 個 chunks")
                return  # Success, exit retry loop

            except Exception as e:
                print(f"[Gemini Text Stream Error] 第 {attempt} 次嘗試失敗：{e}")
                import traceback
                traceback.print_exc()
                
                if attempt == max_retries:
                    print("[Gemini Text Stream Error] 已達最大重試次數，使用降級回應。")
                    # 降級：使用非 streaming 版本
                    try:
                        fallback = await self.reply_gemini_text(user_input, system_instruction, max_retries=1)
                        response_text = fallback.get('response', '⚠️ Gemini 無法回應，請稍後再試。')
                        if char_by_char:
                            for char in response_text:
                                yield char
                        else:
                            yield response_text
                    except Exception as fallback_error:
                        print(f"[Gemini Text Stream] 降級也失敗：{fallback_error}")
                        error_msg = "⚠️ Gemini 無法回應，請稍後再試。"
                        if char_by_char:
                            for char in error_msg:
                                yield char
                        else:
                            yield error_msg
                    return
                await asyncio.sleep(retry_delay)

    async def reply_gemini_text(
        self, user_input: str, system_instruction: str,
        max_retries: int = 3, retry_delay: float = 2.0
    ):
        """Non-streaming version for text generation"""
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[Content(role="user", parts=[Part(text=user_input)])],
                    config=GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        top_k=1,
                        top_p=0.1,
                        max_output_tokens=512,
                    ),
                )

                return {
                    "response": response.text,
                    "total_token_count": response.usage_metadata.total_token_count if response.usage_metadata else 0,
                    "reply_time": round(time.time() - start_time, 2),
                }

            except Exception as e:
                print(f"[Gemini Text Error] 第 {attempt} 次嘗試失敗：{e}")
                if attempt == max_retries:
                    print("[Gemini Text Error] 已達最大重試次數，放棄重試。")
                    return {
                        "response": "⚠️ Gemini 無法回應，請稍後再試。",
                        "total_token_count": 0,
                        "reply_time": 0.0,
                    }
                await asyncio.sleep(retry_delay)

    #現在用這個
    async def GPT41_mini_response(self, messages, max_tokens=3000, json_mode=False):

        try:
            if json_mode:
                response = await self.openai_client_gpt41_mini.chat.completions.create(
                    model=self.model_gpt41_mini,
                    messages=messages,
                    temperature=0,
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                    stream=False,
                )
            else:

                response = await self.openai_client_gpt41_mini.chat.completions.create(
                    model=self.model_gpt41_mini,
                    messages=messages,
                    temperature=0,
                    max_tokens=max_tokens,
                    stream=False,
                )
        except Exception as e:
            print({"GPT4_response error": e})

        return response.choices[0].message.content

    #現在用這個
    async def GPT41_mini_response_functions(
        self, messages, functions, function_call, max_tokens=1000
    ):
        try:
            response = await self.openai_client_gpt41_mini.chat.completions.create(
                model=self.model_gpt41_mini,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
                functions=functions,
                function_call=function_call,
            )
        except Exception as e:
            print({"GPT4_response_functions error": e})

        return response.choices[0].message

    def extract_braces_content(self, text: str) -> list:
        return json.loads(re.findall(r"\{[^}]+\}", text, re.DOTALL)[0])


# if __name__ == "__main__":
#     import os
#     import config_loader as config_loader

#     os.environ["CURRENT_ENV"] = "dev"
#     env = os.environ.get("CURRENT_ENV", "dev")
#     config_loader.env_config = config_loader.load_config()
#     cfg = config_loader.env_config
#     print(cfg.get("cosmos").get("database_name"))

#     base_service = BaseService(cfg)

    # print(await base_service.GPT4_response(
    #     [
    #         {"role":"user","content":'''Hi'''}
    #     ]
    #     ))
