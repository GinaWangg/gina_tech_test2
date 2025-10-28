import re
import os
import pickle
import logging
import time
from pathlib import Path
from src.core.technical_support_async import *

# 使用絕對路徑，基於專案根目錄
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_PATH = _PROJECT_ROOT / "data" / "ts_rag_open_remarks_mappings.xlsx"

ts_rag_open_remarks_mappings = pd.read_excel(str(_DATA_PATH))
ts_rag_open_remarks_mappings = ts_rag_open_remarks_mappings.set_index("lang")["opening_remarks"].to_dict()

class ServiceProcess:

    def __init__(self, system_code, container):
        self.ts_rag = TSRAG(config=container.cfg)
        self.ts_pl = TSProductLine(config=container.cfg, productline_name_map=container.productline_name_map)
        self.redis_config = container.redis_config
        self.system_code = system_code
        self.container = container

    # @async_timer.timeit
    async def technical_support_hint_create(
        self,
        kb_list,
        top1_kb,
        top1_kb_sim,
        lang,
        search_info,
        his_inputs,
        system_code,
        site,
        config,
    ):
        """ """
        top1_hint_search_result = await self.redis_config.get_hint_simiarity(
            search_info
        )
        """ hint of Techinical Support top2,3 KB  """
        relative_questions = []
        if len(kb_list):
            for i, kb in enumerate(kb_list):
                """if top1 kb is highly simiar to search info then use hint vector.
                else use index 1.
                """
                if i == 0 and kb == top1_hint_search_result["faq"]:
                    key = str(top1_hint_search_result["hints_id"]) + "_" + site
                    index_suffix = (
                        "2" # "gina"
                        # "2" if self.container.rag_hint_id_index_mapping.get(key)["index"] == 1 else "1"
                    )
                else:
                    index_suffix = "1"

                # 若對應不到hint則跳過
                rag_key = f"{kb}_{site}_{index_suffix}"
                if rag_key in self.container.rag_mappings:
                    relative_questions.append(self.container.rag_mappings.get(rag_key).copy())

            """ deal with the link between diffenet site"""
            for i in range(len(relative_questions)):
                if system_code.lower() == "rog":
                    relative_questions[i]["link"] = relative_questions[i]["ROG_link"]
                else:
                    relative_questions[i]["link"] = relative_questions[i]["ASUS_link"]

                # print(i, relative_questions[i]["ASUS_link"])
                del relative_questions[i]["ASUS_link"]
                del relative_questions[i]["ROG_link"]
        ''' Open Remarks By Language '''
        open_remarks = ts_rag_open_remarks_mappings.get(lang)
        """ top 1 kb content, summary """
        content = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("content")
        summary = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("summary")
        title = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("title")
        ASUS_link = f"https://www.asus.com/{site}/support/FAQ/{top1_kb}"
        ROG_link = f"https://rog.asus.com/{site}/support/FAQ/{top1_kb}"

        tecnical_response, response_info = await self.ts_rag.technical_rag(
            top1_kb,
            top1_kb_sim,
            title,
            content,
            summary,
            his_inputs[-1],
            lang=lang,
            site=site,
        )

        """ rag_content is hint of Technical Support top1 KB """
        rag_response = {
            "rag_response": tecnical_response,
            "rag_content": {
                "ask_content": open_remarks + "\n" + 
                tecnical_response,
                "title": title,
                "content": content,
                "link": ROG_link if system_code.lower() == "rog" else ASUS_link,
            },
            "relative_questions": relative_questions,
            "response_info": response_info,
        }
        return rag_response

    # @async_timer.timeit
    async def technical_support_hint_follow_up(
        self,
        kb_list,
        top1_kb,
        top1_kb_sim,
        lang,
        search_info,
        his_inputs,
        system_code,
        site,
        last_question,
        last_answer=None,
        last_kb=None,
    ):
        """ """
        top1_hint_search_result = await self.redis_config.get_hint_simiarity(
            search_info
        )
        """ hint of Techinical Support top2,3 KB  """
        relative_questions = []
        if len(kb_list):
            for i, kb in enumerate(kb_list):
                """if top1 kb is highly simiar to search info then use hint vector.
                else use index 1.
                """
                if i == 0 and kb == top1_hint_search_result["faq"]:
                    key = str(top1_hint_search_result["hints_id"]) + "_" + site
                    index_suffix = (
                        "2" if self.container.rag_hint_id_index_mapping.get(key)["index"] == 1 else "1"
                    )
                else:
                    index_suffix = "1"

                # 若對應不到hint則跳過
                rag_key = f"{kb}_{site}_{index_suffix}"
                if rag_key in self.container.rag_mappings:
                    relative_questions.append(self.container.rag_mappings.get(rag_key).copy())

            """ deal with the link between diffenet site"""
            for i in range(len(relative_questions)):
                if system_code.lower() == "rog":
                    relative_questions[i]["link"] = relative_questions[i]["ROG_link"]
                else:
                    relative_questions[i]["link"] = relative_questions[i]["ASUS_link"]

                # print(i, relative_questions[i]["ASUS_link"])
                del relative_questions[i]["ASUS_link"]
                del relative_questions[i]["ROG_link"]
        ''' Open Remarks By Language '''
        open_remarks = ts_rag_open_remarks_mappings.get(lang)
        """ top 1 kb content, summary """
        content = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("content")
        summary = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("summary")
        title = self.container.KB_mappings.get(str(top1_kb) + "_" + lang).get("title")
        ASUS_link = f"https://www.asus.com/{site}/support/FAQ/{top1_kb}"
        ROG_link = f"https://rog.asus.com/{site}/support/FAQ/{top1_kb}"

        last_content = self.container.KB_mappings.get(str(last_kb) + "_" + lang).get("content")
        last_summary = self.container.KB_mappings.get(str(last_kb) + "_" + lang).get("summary")
        last_title = self.container.KB_mappings.get(str(last_kb) + "_" + lang).get("title")

        tecnical_response, response_info = await self.ts_rag.follow_up_rag(
            top1_kb=top1_kb,
            top1_kb_sim=top1_kb_sim,
            title=title,
            content=content,
            summary=summary,
            last_his_input=his_inputs[-1],
            lang=lang,
            last_question=last_question,
            last_answer=last_answer,
            last_content=last_content,
            last_title=last_title,
            last_summary=last_summary,
        )

        """ rag_content is hint of Technical Support top1 KB """
        rag_response = {
            "rag_response": tecnical_response,
            "rag_content": {
                "ask_content": open_remarks + "\n" + 
                tecnical_response,
                "content": content,
                "title": title,
                "link": ROG_link if system_code.lower() == "rog" else ASUS_link,
            },
            "relative_questions": relative_questions,
            "response_info": response_info,
        }
        return rag_response

    # @timeit_sync
    def _get_top3_productline(self, faqs_wo_pl):
        pl_list, kb_list = self.ts_pl.get_top3_productline(faqs_wo_pl)
        return pl_list, kb_list

    # @async_timer.timeit
    async def technical_support_productline_reask(
        self, user_input, faqs_wo_pl, site, lang, system_code
    ):
        """
        提示句欄位：{
            'id': 提示句對應KB,
            'question': 提示句顯示字樣,
            'rag_response': 在此無意義 暫定空字串,
            'title': 提示句對應產品線,
            'link': 在此無意義 暫定空字串,
        }
        """
        pl_list, kb_list = self._get_top3_productline(faqs_wo_pl)
        service_response = await self.ts_pl.service_response(user_input, pl_list, site, lang)
        relative_questions = []
        for i in range(len(kb_list)):
            similarity = next(
                (item["cosineSimilarity"] for item in faqs_wo_pl if item["kb_no"] == kb_list[i]),
                None  # 找不到就設為 None（可改為 0.0）
            )
            relative_questions.append(
                {
                    "id": kb_list[i],
                    "question": service_response["hint_list"][i],
                    "rag_response": "",
                    "title_name": service_response["pl_name_list"][i],
                    "title": pl_list[i],
                    "similarity": similarity if similarity is not None else 0.0,
                    "icon": service_response["icon_list"][i],
                }
            )

        ask_response = {
            "ask_flag": True,
            "ask_content": service_response.get("ask_content"),
            "function_args": {},
        }
        rag_response = {"rag_response": "", "relative_questions": relative_questions}
        return ask_response, rag_response


    ### 以下為測試工具

    def extract_kb_no(self, reply_text):
        match = re.search(r'kb_no:\s*(\S+)', reply_text)
        if match:
            kb_no_test = match.group(1)
            kb_index = match.start()
            answer = reply_text[:kb_index].strip()
        else:
            answer = reply_text.strip()
            kb_no_test = None

        return kb_no_test, answer
    
    async def process_kb_row_v1(self, item, df_kb, lang):
        kb_no = item["kb_no"]
        content = item["content"]
        emb_sentence = item["emb_sentence"]

        logging.info(f"Processing KB No: {kb_no}, Embedding Sentence: {emb_sentence}, Language: {lang}")

        ### 正常回覆 ###
        reply, total_token_count, reply_time = await self.ts_rag.reply_with_faq_gemini(
            content=content,
            last_his_input=emb_sentence,
            lang=lang
        )
        ### longcontext ###
        reply_all, total_token_count_all, reply_time_all = await self.ts_rag.reply_with_faq_gemini_test(
            content=df_kb,
            last_his_input=emb_sentence,
            lang=lang
        )
        kb_no_all, answer_all = self.extract_kb_no(reply_all)

        ### top_n回覆 ###
        top_kb_raw = await self.redis_config.get_faq(
            search_info=emb_sentence,
            site=item["websitecode"],
            productLine="notebook",
            top_n=10
        )
        df_top_kb = pd.DataFrame(top_kb_raw)
        df_top_kb = df_top_kb[pd.to_numeric(df_top_kb['cosineSimilarity'], errors='coerce') >= 0.6].reset_index(drop=True)
        top_kb = df_top_kb[['faq', 'cosineSimilarity']].to_dict(orient="records")
        top_kb_json = df_top_kb.to_json(orient="records", force_ascii=False)

        reply_test, total_token_count_test, reply_time_test = await self.ts_rag.reply_with_faq_gemini_test(
            content=top_kb_json,
            last_his_input=emb_sentence,
            lang=lang
        )
        kb_no_test, answer = self.extract_kb_no(reply_test)


        return {
            "emb_sentence": emb_sentence,
            "kb_no": kb_no,
            "reply_time": reply_time,
            "tokens" : total_token_count,
            "reply": reply,
            "kb_no_test": kb_no_test,
            "reply_time_test": reply_time_test,
            "tokens_test": total_token_count_test,
            "reply_test": answer,
            "kb_no_all": kb_no_all,
            "reply_time_all": reply_time_all,
            "tokens_all": total_token_count_all,
            "reply_all": answer_all,
            "top_kb": top_kb
        }
    
    async def process_kb_row_dev(self, item, df_kb):
        kb_no = item["top1_kb"]
        content = item["content"]
        emb_sentence = item["emb_sentence"]
        site = item["websitecode"]
        productLine = item["productline"]

        lang = self.container.cosmos_settings.get_language_by_websitecode(site)

        logging.info(f"Processing KB No: {kb_no}, Embedding Sentence: {emb_sentence}, Language: {lang}")

        ### 正常回覆 ###
        response = await self.ts_rag.reply_with_faq_gemini(
            content=content,
            last_his_input=emb_sentence,
            lang=lang
        )

        ### top_n回覆 ###
        top_kb_raw = await self.redis_config.get_faq(
            search_info=emb_sentence,
            site=site,
            productLine=productLine,
            top_n=10
        )
        top_kb = [
            {"kb_no": kb, "cosineSimilarity": sim}
            for kb, sim in zip(
                top_kb_raw.get("faq", []),
                top_kb_raw.get("cosineSimilarity", [])
            )
        ]
        kb_articles = []
        for entry in top_kb:
            if entry["cosineSimilarity"] >= 0.6:
                kb_data = self.container.cosmos_settings.get_kb_article(lang, entry["kb_no"])
                if kb_data:
                    kb_articles.append({
                        "kb_no": entry["kb_no"],
                        "title": kb_data.get("title", ""),
                        "content": kb_data.get("content", "")
                    })
                else:
                    kb_data = self.container.cosmos_settings.get_kb_article("en-us", entry["kb_no"])
                    kb_articles.append({
                        "kb_no": entry["kb_no"],
                        "title": kb_data.get("title", ""),
                        "content": kb_data.get("content", "")
                    })
            else:
                kb_articles.append({
                    "kb_no": entry["kb_no"],
                    "title": "",
                    "content": ""
                })
                
        response_test = await self.ts_rag.reply_with_faq_gemini_test(
            content=kb_articles,
            last_his_input=emb_sentence,
            lang=lang
        )

        ### longcontext ###
        kb_records = df_kb[df_kb["productline"] == productLine].to_dict(orient="records")

        response_all = await self.ts_rag.reply_with_faq_gemini_test(
            content=kb_records,
            last_his_input=emb_sentence,
            lang=lang
        )

        return {
            "emb_sentence": emb_sentence,
            "kb_no": kb_no,
            "reply_time": response['reply_time'],
            "tokens" : response['total_token_count'],
            "reply": response['response'].answer,
            "kb_no_test": response_test['response'].kb_no,
            "reply_time_test": response_test['reply_time'],
            "tokens_test": response_test['total_token_count'],
            "reply_test": response_test['response'].answer,
            "kb_no_all": response_all['response'].kb_no,
            "reply_time_all": response_all['reply_time'],
            "tokens_all": response_all['total_token_count'],
            "reply_all": response_all['response'].answer,
            "top_kb": top_kb
        }

    async def process_kb_row(self, item, df_kb):
        kb_no = item["top1_kb"]
        content = item["content"]
        emb_sentence = item["emb_sentence"]
        site = item["websitecode"]
        productLine = item["productline"]

        lang = self.container.cosmos_settings.get_language_by_websitecode(site)
        logging.info(f"Processing KB No: {kb_no}, Embedding Sentence: {emb_sentence}, Language: {lang}")

        ## 正常回覆
        response = await self.ts_rag.reply_with_faq_gemini(content=content, last_his_input=emb_sentence, lang=lang)
        logging.info(f"Normal response for KB No: {kb_no} completed.")
        ## top_n回覆
        top_kb_raw = await self.redis_config.get_faq(search_info=emb_sentence, site=site, productLine=productLine, top_n=10)
        top_kb = [{"kb_no": kb, "cosineSimilarity": sim} for kb, sim in zip(top_kb_raw.get("faq", []), top_kb_raw.get("cosineSimilarity", []))]
        
        kb_articles = []
        for entry in top_kb:
            if entry["cosineSimilarity"] >= 0.6:
                kb_data = self.container.cosmos_settings.get_kb_article(lang, entry["kb_no"]) or self.container.cosmos_settings.get_kb_article("en-us", entry["kb_no"])
                kb_articles.append({
                    "kb_no": entry["kb_no"],
                    "title": kb_data.get("title", ""),
                    "content": kb_data.get("content", "")
                })
            else:
                kb_articles.append({"kb_no": entry["kb_no"], "title": "", "content": ""})

        response_test = await self.ts_rag.reply_with_faq_gemini_test(content=kb_articles, last_his_input=emb_sentence, lang=lang)
        logging.info(f"Top-N response for KB No: {kb_no} completed.")
        ## longcontext 回覆
        kb_records = df_kb[(df_kb["productline"] == productLine) & (df_kb["lang"] == lang)].to_dict(orient="records")
        response_all = await self.ts_rag.reply_with_faq_gemini_test(content=kb_records, last_his_input=emb_sentence, lang=lang)
        logging.info(f"Long-context response for KB No: {kb_no} completed.")

        # 儲存 pickle 檔案
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", emb_sentence.strip())[:100]
        output_pickle_path = f"D:/vscode/PROJECTS/ts_agent/output/{safe_name}.pkl"

        result = {
            "file_name": output_pickle_path,
            "emb_sentence": emb_sentence,
            "productline": productLine,
            "kb_no": kb_no,
            "reply_time": response['reply_time'],
            "tokens": response['total_token_count'],
            "reply": response['response'].answer,
            "kb_no_test": response_test['response'].kb_no,
            "reply_time_test": response_test['reply_time'],
            "tokens_test": response_test['total_token_count'],
            "reply_test": response_test['response'].answer,
            "kb_no_all": response_all['response'].kb_no,
            "reply_time_all": response_all['reply_time'],
            "tokens_all": response_all['total_token_count'],
            "reply_all": response_all['response'].answer,
            "top_kb": top_kb
        }

        # df_output = pd.DataFrame(result)
        # df_output = pd.DataFrame([result])
        os.makedirs(os.path.dirname(output_pickle_path), exist_ok=True)
        with open(output_pickle_path, "wb") as f:
            pickle.dump(result, f)

        return result
    
    async def count_process_time(self, item, df_kb):
        kb_no = item["top1_kb"]
        content = item["content"]
        emb_sentence = item["emb_sentence"]
        site = item["websitecode"]
        productLine = item["productline"]

        lang_start = time.time()
        lang = self.container.cosmos_settings.get_language_by_websitecode(site)
        lang_time = time.time() - lang_start
        logging.info(f"language retrieval time for KB No: {kb_no} is {lang_time:.2f} seconds")
        # logging.info(f"Processing KB No: {kb_no}, Embedding Sentence: {emb_sentence}, Language: {lang}")

        ## 正常回覆
        one_start = time.time()
        kb_raw = await self.redis_config.get_faq(search_info=emb_sentence, site=site, productLine=productLine, top_n=1)
        primary_kb_no = (kb_raw.get("faq") or [None])[0]
        primary_content  = (self.container.cosmos_settings.get_kb_article(lang, primary_kb_no) or self.container.cosmos_settings.get_kb_article("en-us", primary_kb_no) or {}).get("content", "")
        # response = await self.ts_rag.reply_with_faq_gemini(content=content, last_his_input=emb_sentence, lang=lang)
        one_time = time.time() - one_start
        logging.info(f"Normal response for KB No: {kb_no} completed in {one_time:.2f} seconds")
        # logging.info(f"Normal response for KB No: {kb_no} completed.")
        ## top_n回覆
        two_start = time.time()
        top_kb_raw = await self.redis_config.get_faq(search_info=emb_sentence, site=site, productLine=productLine, top_n=10)
        top_kb = [{"kb_no": kb, "cosineSimilarity": sim} for kb, sim in zip(top_kb_raw.get("faq", []), top_kb_raw.get("cosineSimilarity", []))]
        
        kb_articles = []
        for entry in top_kb:
            if entry["cosineSimilarity"] >= 0.6:
                kb_data = self.container.cosmos_settings.get_kb_article(lang, entry["kb_no"]) or self.container.cosmos_settings.get_kb_article("en-us", entry["kb_no"])
                kb_articles.append({
                    "kb_no": entry["kb_no"],
                    "title": kb_data.get("title", ""),
                    "content": kb_data.get("content", "")
                })
            else:
                kb_articles.append({"kb_no": entry["kb_no"], "title": "", "content": ""})

        # response_test = await self.ts_rag.reply_with_faq_gemini_test(content=kb_articles, last_his_input=emb_sentence, lang=lang)
        two_time = time.time() - two_start
        logging.info(f"Top-N response for KB No: {kb_no} completed in {two_time:.2f} seconds")
        # logging.info(f"Top-N response for KB No: {kb_no} completed.")
        ## longcontext 回覆
        three_start = time.time()
        kb_records = df_kb[(df_kb["productline"] == productLine) & (df_kb["lang"] == lang)].to_dict(orient="records")
        # response_all = await self.ts_rag.reply_with_faq_gemini_test(content=kb_records, last_his_input=emb_sentence, lang=lang)
        three_time = time.time() - three_start
        logging.info(f"Long-context response for KB No: {kb_no} completed in {three_time:.2f} seconds")
        # logging.info(f"Long-context response for KB No: {kb_no} completed.")

        # 儲存 pickle 檔案
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", emb_sentence.strip())[:100]
        output_pickle_path = f"D:/vscode/PROJECTS/ts_agent/output/{safe_name}.pkl"

        result = {
            "file_name": output_pickle_path,
            "emb_sentence": emb_sentence,
            "productline": productLine,
            "kb_no": kb_no,
            "lang_time": lang_time,
            "reply_time": one_time,
            "reply_time_test": two_time,
            "reply_time_all": three_time,
            "top_kb": top_kb
        }

        # df_output = pd.DataFrame(result)
        # df_output = pd.DataFrame([result])
        os.makedirs(os.path.dirname(output_pickle_path), exist_ok=True)
        with open(output_pickle_path, "wb") as f:
            pickle.dump(result, f)

        return result
    

