import torch
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*resume_download.*")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))

# Model configurations
MODEL_NAME = 'BM-K/KoSimCSE-roberta'
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ChromaDB configurations - ���� ��� ��� �� �ڷ���Ʈ�� ��Ȱ��ȭ
CHROMA_DB_PATH = os.path.join(CURRENT_DIR, "chroma_db")
COLLECTION_NAMES = {
    "question": "q_embeddings",
    "snippet": "s_embeddings", 
    "keyword": "k_embeddings"
}

# Data file paths - ���� ��� ���
DATA_FILES = {
    "question": os.path.join(CURRENT_DIR, "VectorDB", "q_data.pkl"),
    "snippet": os.path.join(CURRENT_DIR, "VectorDB", "s_data.pkl"),
    "keyword": os.path.join(CURRENT_DIR, "VectorDB", "k_data.pkl")
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