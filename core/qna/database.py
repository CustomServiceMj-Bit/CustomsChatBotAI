"""
ChromaDB database management for RAG system
"""
import pickle
import chromadb
from chromadb.config import Settings
from core.qna.config import CHROMA_DB_PATH, COLLECTION_NAMES, DATA_FILES
import logging

# ChromaDB 로그 레벨 설정하여 중복 추가 메시지 숨기기
logging.getLogger("chromadb").setLevel(logging.ERROR)

class ChromaDBManager:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory=CHROMA_DB_PATH, 
            anonymized_telemetry=False,
            is_persistent=True
        ))
        self.collections = {}
        self._initialize_collections()
        
    def _initialize_collections(self):
        """Initialize ChromaDB collections"""
        for key, collection_name in COLLECTION_NAMES.items():
            self.collections[key] = self.client.get_or_create_collection(collection_name)
            
    def load_data_from_pickle(self):
        """Load data from pickle files"""
        data = {}
        for key, file_path in DATA_FILES.items():
            with open(file_path, "rb") as f:
                data[key] = pickle.load(f)
        return data
        
    def add_to_collection(self, collection_key, data):
        """Add data to collection, avoiding duplicate IDs"""
        collection = self.collections[collection_key]
        
        # 기존 ID들 확인
        existing_ids = set(collection.get()['ids']) if collection.count() > 0 else set()
        
        # 새로운 데이터 중 중복되지 않는 것만 필터링
        new_documents = []
        new_embeddings = []
        new_metadatas = []
        new_ids = []
        
        for i, doc_id in enumerate(data["ids"]):
            if doc_id not in existing_ids:
                new_documents.append(data["documents"][i])
                new_embeddings.append(data["embeddings"][i])
                new_metadatas.append(data["metadatas"][i])
                new_ids.append(doc_id)
        
        # 새로운 데이터가 있는 경우에만 추가
        if new_ids:
            collection.add(
                documents=new_documents,
                embeddings=new_embeddings,
                metadatas=new_metadatas,
                ids=new_ids
            )
        
    def setup_database(self):
        """Load data from pickle files and populate collections"""
        data = self.load_data_from_pickle()
        
        for key in ["question", "snippet", "keyword"]:
            self.add_to_collection(key, data[key])  
                  
    def get_collection(self, collection_key):
        """Get collection by key"""
        return self.collections[collection_key]