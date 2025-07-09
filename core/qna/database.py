"""
ChromaDB database management for RAG system
"""
import pickle
import chromadb
from chromadb.config import Settings
from config import CHROMA_DB_PATH, COLLECTION_NAMES, DATA_FILES


class ChromaDBManager:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory=CHROMA_DB_PATH, 
            anonymized_telemetry=False
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

        collection = self.collections[collection_key]
        collection.add(
            documents=data["documents"],
            embeddings=data["embeddings"],
            metadatas=data["metadatas"],
            ids=data["ids"]
        )
        
    def setup_database(self):
        """Load data from pickle files and populate collections"""
        data = self.load_data_from_pickle()
        
        for key in ["question", "snippet", "keyword"]:
            self.add_to_collection(key, data[key])  
                  
    def get_collection(self, collection_key):
        """Get collection by key"""
        return self.collections[collection_key]