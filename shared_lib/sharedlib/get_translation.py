# --------------------------------- Import Modules --------------------------------------------------
import json
import re
import html
import asyncio
from opencc import OpenCC

from google.oauth2 import service_account
from google.cloud import translate_v2 as translate
from langid.langid import LanguageIdentifier, model

from sharedlib.call_llm_openai import CallOpenAI

# --------------------------------- Function Definitions --------------------------------------------

# Translator
class Translator(CallOpenAI):
    _instance = None
     
    @classmethod
    def get_instance(cls, model_name=None, info=None, client=None):
        """Returns the Singleton instance of the Translator class. If the instance doesn't exist, it is created."""
        
        if cls._instance is None:
            cls._instance = cls(model_name=model_name, info=info, client=client)
        return cls._instance
    
    def __init__(self, 
                 model_name: str = 'openai_gpt41mini_paygo_eu',
                 info: str = None,
                 client=None):
        """
        初始化翻譯器
        
        Args:
            model_name (str): OpenAI 模型名稱
            credentials_path (str): Google Translate API 憑證檔案路徑
        """
        super().__init__(model_name=model_name, client=client)
        self.model = model_name

        SCOPES = [
            "https://www.googleapis.com/auth/cloud-platform",
        ]
        creds = service_account.Credentials.from_service_account_info(info).with_scopes(SCOPES)
        self.translate_client = translate.Client(credentials=creds)

        # 建立服務
        # self.translate_client = translate.Client.from_service_account_json(self.key_path)
        self.identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self._opencc = OpenCC("s2twp")

    def _handle_gpt_error_response(self, user_input: str):
        return json.dumps({"en_question": user_input})

    def _clean_text(self, query: str): 
        clean_output = html.unescape(query)
        clean_output = re.sub(r'<div><br></div><div>', ', ', clean_output)
        return re.sub(r'\n|<br>|<div>|</div>', ' ', clean_output)

    def _translate_text(self, target, text):
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        result = self.translate_client.translate(text, target_language=target)
        return result.get('translatedText')

    # @timed
    async def get_translation(self, user_input=None):
        system_prompt = '''
You are a translator, user will provide a question, you don't have to understand question, just please translate the question into English and reply to en_question in jsonl format. If the question cannot be translated into English or has been English already, please fill in the original question.
Here are some knowledge you need to know
1.If user said Notebook have second screen or display controller, it is called "sreenPad"
2. Ignore bullet points and typo error from user input.
3. replace the word laptop by notebook and replace the word screen by display in your english sentence.
4. no question mark, no bullet points in your english sentence.
5. respond original question if you cannot translate the phrase.

Here are the output samples. Always respond with JSONL format and answer in English.

1.question: 路由器的連線品質很差，要怎麼改善?"
jsonl sample:
{"en_question":"How to set up the network for a newly purchased router?"}

2.question: feel heat from vents"
jsonl sample:
{"en_question":"feel heat from vents"}
3.question: Error Code: 0x00000010"
jsonl sample:
{"en_question":"Error Code: 0x00000010"}
'''
        user_prompt = f'''
Please respond in JSONL format, and the en_question field should be filled with the question translated into English.
If the question cannot be translated into English or has been English already, please fill in the original question.
The question is as follows: {user_input}.

'''

        try:
            result = await self.call_gpt4o(
                sys_prompt = system_prompt, 
                user_prompt = user_prompt, 
                json_mode=True)
        except Exception:
            result = self._handle_gpt_error_response(user_input)

        try:
            response = json.loads(result).get('en_question', '').replace('..', '.')
        except (json.JSONDecodeError, TypeError):
            response = user_input

        is_en, prob = self.identifier.classify(response)
        if (is_en != 'en') or (is_en == 'en' and prob <= 0.8):
            response = self._translate_text('en', response)

        return self._clean_text(response)

    def translate_sync(self, text: str) -> str:
        return asyncio.run(self.get_translation(text))

# --------------------------------- Example Usage -------------------------------------------

# if __name__ == "__main__":
#     get_trans = Translator()
#     user_query = "請推薦筆電"

#     async def main():
#         result = await get_trans.get_translation(user_query)
#         print(result)
    
#     await main()