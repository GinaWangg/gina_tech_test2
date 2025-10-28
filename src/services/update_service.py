# src/services/update_service.py

import pickle


class UpdateService:
    """處理資料更新的服務層"""
    
    def __init__(self, containers):
        self.containers = containers
        
    async def update_technical_rag(self):
        """更新技術 RAG 資料"""
        container_name = "sample_question"
        container = self.containers.lookup_db.get_container_client(container_name)
        query = "SELECT * FROM c"
        results = container.query_items(query, enable_cross_partition_query=True)

        new_rag_mappings, new_rag_hint_id_index_mapping = {}, {}
        ASUS_link = "https://www.asus.com/{}/support/FAQ/{}"
        ROG_link = "https://rog.asus.com/{}/support/FAQ/{}"

        for item in results:
            key = f"{item.get('kb_no')}_{item.get('websitecode')}_{item.get('index')}"
            new_rag_mappings[key] = {
                "id": item.get("id"),
                "question": item.get("question"),
                "rag_response": item.get("rag"),
                "title": item.get("title"),
                "ASUS_link": ASUS_link.format(item.get("websitecode"), item.get("kb_no")),
                "ROG_link": ROG_link.format(item.get("websitecode"), item.get("kb_no"))
            }
            key2 = f"{item.get('id')}_{item.get('websitecode')}"
            new_rag_hint_id_index_mapping[key2] = {
                "index": item.get("index"),
                "rag": item.get("rag")
            }

        self.containers.rag_mappings = new_rag_mappings
        self.containers.rag_hint_id_index_mapping = new_rag_hint_id_index_mapping

        # 儲存到檔案
        with open("config/rag_hint_id_index_mapping.pkl", "wb") as file:
            pickle.dump(self.containers.rag_hint_id_index_mapping, file)
        with open("config/rag_mappings.pkl", "wb") as file:
            pickle.dump(self.containers.rag_mappings, file)

        return {"message": "rag_mappings update success"}

    def update_website_botname(self):
        """更新網站機器人名稱對應"""
        container_name = "all_websitecode_productline"
        container = self.containers.lookup_db.get_container_client(container_name)

        query = """SELECT * FROM c"""
        results = container.query_items(query, enable_cross_partition_query=True)

        new_PL_mappings = {}
        new_productline_name_map = {}
        for item in results:
            if not new_PL_mappings.get(item.get("websiteCode")):
                new_PL_mappings[item.get("websiteCode")] = set()
                new_productline_name_map[item.get("websiteCode")] = {}
            new_PL_mappings[item.get("websiteCode")].add(item.get("productLine"))
            new_productline_name_map[item.get("websiteCode")][item.get("productLine")] = item.get("productLine_name")

        self.containers.PL_mappings = new_PL_mappings
        self.containers.productline_name_map = new_productline_name_map
        
        return {"message": "PL_mappings update success"}

    def update_KB(self):
        """更新知識庫資料"""
        container_name = "ApChatbotKnowledge"
        container = self.containers.lookup_db.get_container_client(container_name)

        query = """SELECT * FROM c"""
        results = container.query_items(query, enable_cross_partition_query=True)

        new_KB_mappings = {
            f"{item.get('kb_no')}_{item.get('lang')}": {
                "title": item.get("title"),
                "summary": item.get("summary"),
                "content": item.get("content")[:10000],
            }
            for item in results
        }

        self.containers.KB_mappings = new_KB_mappings
        
        # 儲存到檔案
        with open("config/kb_mappings.pkl", "wb") as file:
            pickle.dump(self.containers.KB_mappings, file)
        
        return {"message": "KB_mappings update success"}

    def update_specific_KB(self):
        """更新特定知識庫對應"""
        container_name = "specific_kb_bot_scope"
        container = self.containers.lookup_db.get_container_client(container_name)

        query = """SELECT * FROM c"""
        results = container.query_items(query, enable_cross_partition_query=True)

        new_specific_kb_mappings = {
            f"{item.get('kb_no')}_{item.get('bot_scope')}": {
                "id": item.get("id"),
                "correct_kb_no": int(item.get("correct_kb_no")),
            }
            for item in results
        }

        self.containers.specific_kb_mappings = new_specific_kb_mappings
        
        return {"message": "Specific_KB_mappings update success"}
