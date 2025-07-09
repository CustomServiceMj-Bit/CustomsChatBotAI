import torch

# Model configurations
MODEL_NAME = 'BM-K/KoSimCSE-roberta'
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ChromaDB configurations
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAMES = {
    "question": "q_embeddings",
    "snippet": "s_embeddings", 
    "keyword": "k_embeddings"
}

# Data file paths
DATA_FILES = {
    "question": "VectorDB/q_data.pkl",
    "snippet": "VectorDB/s_data.pkl",
    "keyword": "VectorDB/k_data.pkl"
}

# Search configurations
DEFAULT_TOP_K = 10
DEFAULT_WEIGHTS = {
    "question": 0.4,
    "snippet": 0.3,
    "keyword": 0.3
}

# Generation configurations
OPENAI_MODEL = "gpt-4"
GENERATION_TEMPERATURE = 0.2
MAX_REFERENCE_DOCS = 5