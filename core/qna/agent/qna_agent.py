from core.shared.states.states import CustomsAgentState
from core.qna.main import RAGSystem

def qna_agent(state: CustomsAgentState) -> CustomsAgentState:
    """QNA RAG 에이전트 - 실제 RAG 시스템 사용"""
    
    # RAG 시스템 초기화 및 데이터베이스 설정
    rag_system = RAGSystem()
    rag_system.setup_database()
    
    # RAG 시스템을 사용하여 답변 생성
    answer = rag_system.search_and_generate(
        query=state["query"],
        top_k=5,
        show_details=False
    )
    
    state["final_response"] = answer
    state["intermediate_results"]["qna"] = {
        "response": answer,
        "query": state["query"]
    }
    
    return state