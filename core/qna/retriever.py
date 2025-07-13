"""
RAG retrieval system with weighted search using VectorDB pickle files
"""
import torch
import pickle
import numpy as np
from core.qna.encoder import TextEncoder, cosine_score
from core.qna.config import DATA_FILES, DEFAULT_TOP_K, DEFAULT_WEIGHTS


class VectorDBRetriever:
    def __init__(self):
        self.encoder = TextEncoder()
        self.data = self._load_vector_data()
        
    def _load_vector_data(self):
        """Load data from VectorDB pickle files"""
        data = {}
        for key, file_path in DATA_FILES.items():
            with open(file_path, "rb") as f:
                data[key] = pickle.load(f)
        return data
        
    def search_with_weights(self, query, top_k=DEFAULT_TOP_K, 
                          w_q=DEFAULT_WEIGHTS["question"], 
                          w_s=DEFAULT_WEIGHTS["snippet"], 
                          w_k=DEFAULT_WEIGHTS["keyword"]):
        """
        Perform weighted search across question, snippet, and keyword data
        
        Args:
            query: str - search query
            top_k: int - number of top results to return
            w_q, w_s, w_k: float - weights for question, snippet, keyword collections
            
        Returns:
            list: ranked search results with scores
        """
        query_embedding = torch.tensor(self.encoder.encode(query)[0], dtype=torch.float32)
        scores = {}
        
        def score_data(data_key, weight, score_idx):
            data = self.data[data_key]
            embeddings = data["embeddings"]
            metadatas = data["metadatas"]
            
            for i in range(len(embeddings)):
                id_ = data["ids"][i]
                emb = torch.tensor(embeddings[i], dtype=torch.float32)
                score = cosine_score(query_embedding, emb)
                
                if id_ not in scores:
                    scores[id_] = [0.0, 0.0, 0.0, 0.0]  # total, q, s, k
                scores[id_][0] += weight * score
                scores[id_][score_idx] = score
        
        # Score each data type
        score_data("question", w_q, 1)
        score_data("snippet", w_s, 2)  
        score_data("keyword", w_k, 3)
        
        # Sort by total score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
        
        # Build final results
        final_results = []
        for id_, (total, q_score, s_score, k_score) in sorted_scores[:top_k]:
            # Get metadata from question data (assuming it has the most complete info)
            question_data = self.data["question"]
            id_index = question_data["ids"].index(id_) if id_ in question_data["ids"] else 0
            meta = question_data["metadatas"][id_index]
            
            final_results.append({
                "index": id_,
                "question": meta["question"],
                "answer": meta["answer"],
                "entities": meta["entities"],
                "score_combined": total,
                "score_question": q_score,
                "score_snippet": s_score,
                "score_keyword": k_score
            })
            
        return final_results


class RAGRetriever:
    def __init__(self):
        self.vector_retriever = VectorDBRetriever()
        
    def search_with_weights(self, query, top_k=DEFAULT_TOP_K, 
                          w_q=DEFAULT_WEIGHTS["question"], 
                          w_s=DEFAULT_WEIGHTS["snippet"], 
                          w_k=DEFAULT_WEIGHTS["keyword"]):
        """Wrapper for VectorDBRetriever"""
        return self.vector_retriever.search_with_weights(query, top_k, w_q, w_s, w_k)