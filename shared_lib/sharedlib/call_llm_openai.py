# --------------------------------- Import Modules --------------------------------------------------
from openai import AsyncAzureOpenAI

import time
from textwrap import dedent

import asyncio

# ver_openai = 'openai_gpt4o_ptu_jp'
# ver_openai = 'openai_gpt4o_paygo_1120'

# --------------------------------- Function Definitions --------------------------------------------

# CallOpenAI
class CallOpenAI:
    def __init__(self, model_name: str ='openai_gpt41mini_paygo_eu', client=None):
        """initialize OpenAI API client"""
        # 讀 .env
        self.openai_model       = model_name

        # 初始化 Azure OpenAI 非同步客戶端
        self.client = client

    async def call_gpt4o(
            self, 
            sys_prompt,
            user_prompt, 
            json_mode=False, 
            time_out = 5):
        
        """Call GPT-4o API."""
        response_format = {"type": "json_object"} if json_mode else None
        
        messages = [
            {"role": "system", "content": dedent(sys_prompt).strip()}, 
            {"role": "user", "content": dedent(user_prompt).strip()}
        ]

        try:
            response = await asyncio.wait_for(self.client.chat.completions.create(
                model=self.openai_model,             
                messages=messages,
                temperature=0,
                #max_tokens=max_tokens,
                stream=False,
                response_format=response_format,),
                timeout=time_out
            )
            
            return response.choices[0].message.content
        
        except asyncio.TimeoutError:
            print(f'OpenAI API Timeout: {time_out} seconds')

            response = await self.client.chat.completions.create(
                model = self.openai_model,
                messages=messages,
                response_format=response_format,
                temperature=0,
            )
            return response.choices[0].message.content
        
        except:
            time.sleep(0.5)
            response = await self.client.chat.completions.create(
                model = self.openai_model,
                messages=messages,
                response_format=response_format,
                temperature=0, 
            )
            return response.choices[0].message.content
    
    async def call_gpt4o_func(
            self, 
            sys_prompt,
            user_prompt, 
            json_mode=False, 
            tool=None):
        
        """Call GPT-4o API."""
        
        messages = [
            {"role": "system", "content": dedent(sys_prompt).strip()}, 
            {"role": "user", "content": dedent(user_prompt).strip()}
        ]
        
        try:
            
            response = await self.client.chat.completions.create(
                model = self.openai_model,
                messages=messages,
                tools=tool
            )
            return response
        
        except:
            time.sleep(0.5)
            response = await self.client.chat.completions.create(
                model = self.openai_model,
                messages=messages,
                tools=tool
            )
            return response
        

# --------------------------------- Example Usage -------------------------------------------

# if __name__ == "__main__":
#     openai_client = CallOpenAI(version='openai_gpt4o_paygo')

#     async def user_info(inquiry):
#         system_prompt = f'''
#         You are a **Detector AI assistant** responsible for detecting the user inquiry and providing the relevant information.
#         1. product line in the inquiry
#         product line: accessories,motherboards,networking,laptops,phones,gaming-handhelds,zenbo,mini-pcs,desktops,all-in-one-pcs,
#                     servers,graphics-cards,glasses,monitors,nucs,tablets,aiot,wearable-healthcare,iot,power-supply-units,projectors,
#                     processors,storage,utilities,printers
#         2. Order number in the inquiry

#         **Guidelines**:
#         - **Detect** the product line and order number in the inquiry.
#         - If the inquiry contains **both product line and order number**, **return both**.
#         - return the product line only in above list.
#         - If the inquiry contains **only the product line**, **return the product line**.
#         - If the inquiry contains **only the order number**, **return the order number**.
#         - **Return only the JSON object** with the detected information.
#         '''

#         user_prompt = f"""
#         Detect the following user inquiry and provide the relevant information.

#         ## **User Inquiry**:
#         "{inquiry}"

#         Now, provide the classification result in JSON format:
#         ```json
#         {{"prodcutline": ["accessories", "laptops"], "OrderNumber": "1234567890"}}```
#         """
        
#         result = await openai_client.call_gpt4o(
#                     sys_prompt = system_prompt, 
#                     user_prompt = user_prompt,
#                     json_mode=True)
#         return result

#     async def main():
#         inquiry = "有新的電競筆電推薦嗎? 還有我上次訂單電話填錯了我能改嗎 訂單編號: 1234567890"
#         result = await user_info(inquiry)
#         print(result)

#     await main()

