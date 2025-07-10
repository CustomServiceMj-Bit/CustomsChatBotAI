from typing import List, Dict, Any

from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm

# RAG 에이전트용 더미 데이터베이스
class CustomsRAG:
    def __init__(self, vector_db_path: str = "customs_faiss.index", csv_path: str = "customs_data.csv"):
        """
        FAISS 벡터DB와 CSV 데이터를 로드합니다.
        실제 구현에서는 이미 생성된 벡터DB를 로드한다고 가정
        """
        self.embeddings = OpenAIEmbeddings()
        # 더미로 설정 - 실제로는 faiss.read_index(vector_db_path)
        self.vector_db = None
        self.documents = []  # 실제로는 CSV에서 로드
        
        # 더미 데이터
        self.dummy_documents = [
            {"content": "관세는 외국 상품을 수입할 때 부과되는 세금입니다.", "category": "관세기본"},
            {"content": "통관은 물품이 세관을 통과하는 절차입니다.", "category": "통관절차"},
            {"content": "FTA 협정국에서 수입하는 경우 관세 혜택을 받을 수 있습니다.", "category": "FTA"},
        ]
    
    def search_similar_documents(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """유사한 문서를 검색합니다."""
        # 실제로는 FAISS 검색을 수행
        # query_vector = self.embeddings.embed_query(query)
        # scores, indices = self.vector_db.search(query_vector, k)
        
        # 더미 검색 결과
        return self.dummy_documents[:k]
    
def qna_agent(state: CustomsAgentState) -> CustomsAgentState:
    """QNA RAG 에이전트"""
    rag = CustomsRAG()
    llm = get_llm()
    
    # 유사 문서 검색
    similar_docs = rag.search_similar_documents(state["query"])
    
    # 검색된 문서들을 컨텍스트로 구성
    context = "\n".join([f"- {doc['content']}" for doc in similar_docs])
    
    rag_prompt = f"""
    다음 관세청 관련 정보를 참고하여 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요.

    참고 정보:
    {context}

    사용자 질문: {state["query"]}

    답변:
    """
    
    result = llm.invoke([SystemMessage(content=rag_prompt)])
    
    state["final_response"] = result.content
    state["intermediate_results"]["qna"] = {
        "retrieved_docs": similar_docs,
        "response": result.content
    }
    
    return state