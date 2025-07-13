"""
RAG retrieval system with weighted search across multiple collections
"""
import torch
from core.qna.encoder import TextEncoder, cosine_score
from core.qna.database import ChromaDBManager
from core.qna.config import DEFAULT_TOP_K, DEFAULT_WEIGHTS


class RAGRetriever:
    def __init__(self):
        self.encoder = TextEncoder()
        self.db_manager = ChromaDBManager()
        
    def search_with_weights(self, query, top_k=DEFAULT_TOP_K, 
                          w_q=DEFAULT_WEIGHTS["question"], 
                          w_s=DEFAULT_WEIGHTS["snippet"], 
                          w_k=DEFAULT_WEIGHTS["keyword"]):
        """
        Perform weighted search across question, snippet, and keyword collections
        
        Args:
            query: str - search query
            top_k: int - number of top results to return
            w_q, w_s, w_k: float - weights for question, snippet, keyword collections
            
        Returns:
            list: ranked search results with scores
        """
        query_embedding = torch.tensor(self.encoder.encode(query)[0], dtype=torch.float32)
        scores = {}
        
        # Get collections
        col_q = self.db_manager.get_collection("question")
        col_s = self.db_manager.get_collection("snippet")
        col_k = self.db_manager.get_collection("keyword")
        
        def score_collection(collection, weight, score_idx):
            all_data = collection.get(include=["embeddings", "metadatas", "documents"])
            for i in range(len(all_data['ids'])):
                id_ = all_data['ids'][i]
                emb = torch.tensor(all_data['embeddings'][i], dtype=torch.float32)
                score = cosine_score(query_embedding, emb)
                
                if id_ not in scores:
                    scores[id_] = [0.0, 0.0, 0.0, 0.0]  # total, q, s, k
                scores[id_][0] += weight * score
                scores[id_][score_idx] = score
        
        # Score each collection
        score_collection(col_q, w_q, 1)
        score_collection(col_s, w_s, 2)  
        score_collection(col_k, w_k, 3)
        
        # Sort by total score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
        
        # Build final results
        final_results = []
        for id_, (total, q_score, s_score, k_score) in sorted_scores[:top_k]:
            meta = col_q.get(ids=[id_])['metadatas'][0]
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