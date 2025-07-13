from core.shared.states.states import CustomsAgentState
from core.qna.main import RAGSystem
from core.shared.utils.llm import get_llm
from langchain_core.messages import HumanMessage
import re

def compare_responses(llm_response: str, rag_response: str, comparison_llm) -> bool:
    """
    LLM을 사용하여 두 응답의 유사성을 판단합니다.
    
    Args:
        llm_response: LLM 기반 응답
        rag_response: RAG 기반 응답
        comparison_llm: 비교용 LLM 인스턴스
        
    Returns:
        bool: True if responses are similar, False if they differ significantly
    """
    comparison_prompt = f"""다음은 동일한 질문에 대한 두 개의 답변입니다. 
이 두 답변이 내용적으로 유사한지 판단해주세요.

답변 1: {llm_response}

답변 2: {rag_response}

두 답변의 핵심 내용이 유사하거나 동일하다면 "유사함"이라고 답하고, 
내용이 다르거나 모순되거나 추가 정보가 포함되어 있다면 "다름"이라고 답해주세요.

답변:"""

    try:
        comparison_result = comparison_llm.invoke([HumanMessage(content=comparison_prompt)])
        comparison_text = str(comparison_result.content) if hasattr(comparison_result, 'content') else str(comparison_result)
        
        # "유사함"이 포함되어 있으면 True 반환
        return "유사함" in comparison_text or "similar" in comparison_text.lower()
    except Exception as e:
        # LLM 비교 실패 시 기본 로직 사용
        print(f"LLM 비교 실패, 기본 로직 사용: {e}")
        
        # 간단한 키워드 기반 비교
        def extract_keywords(text: str) -> set:
            customs_keywords = [
                '관세', '세금', '수입', '수출', '통관', '신고', '세율', '과세', '면세',
                '반입', '반출', '검사', '검역', '위험물', '금지', '제한', '허가',
                '서류', '증명', '신청', '처리', '기간', '비용', '요금', '부과'
            ]
            
            keywords = set()
            for keyword in customs_keywords:
                if keyword in text:
                    keywords.add(keyword)
            return keywords
        
        llm_keywords = extract_keywords(llm_response.lower())
        rag_keywords = extract_keywords(rag_response.lower())
        
        if llm_keywords and rag_keywords:
            common_keywords = llm_keywords.intersection(rag_keywords)
            total_keywords = llm_keywords.union(rag_keywords)
            similarity = len(common_keywords) / len(total_keywords) if total_keywords else 0
            return similarity >= 0.7
        
        return False

def qna_agent(state: CustomsAgentState) -> CustomsAgentState:
    """QNA 에이전트 - RAG 우선, 부족시 LLM 활용"""
    
    query = state["query"]
    
    # 1. RAG 시스템을 사용한 응답 생성 (1차 우선)
    rag_system = RAGSystem()
    rag_response = rag_system.search_and_generate(
        query=query,
        top_k=5,
        show_details=False
    )
    
    # 2. RAG 응답의 품질 평가
    def evaluate_rag_quality(rag_response: str, query: str) -> bool:
        """LLM을 사용하여 RAG 응답이 충분한 정보를 제공하는지 평가"""
        llm = get_llm()
        
        evaluation_prompt = f"""다음은 사용자의 질문과 RAG 시스템이 제공한 답변입니다.
이 답변이 사용자의 질문에 대해 충분하고 정확한 정보를 제공하는지 판단해주세요.

사용자 질문: {query}

RAG 답변: {rag_response}

다음 중 하나에 해당하면 "부족함"이라고 답하고, 그렇지 않으면 "충분함"이라고 답해주세요:

1. 답변이 너무 짧거나 구체적이지 않은 경우
2. "정확한 정보를 제공할 수 없다", "참고할 수 있는 문서가 없다" 등의 문구가 포함된 경우
3. 질문에 대한 구체적인 답변이 아닌 일반적인 설명만 있는 경우
4. 문서에 없는 내용을 임의로 생성했다고 명시된 경우

판단 결과:"""

        try:
            evaluation_result = llm.invoke([HumanMessage(content=evaluation_prompt)])
            evaluation_text = str(evaluation_result.content) if hasattr(evaluation_result, 'content') else str(evaluation_result)
            
            # "부족함"이 포함되어 있으면 False 반환
            return "부족함" not in evaluation_text and "insufficient" not in evaluation_text.lower()
            
        except Exception as e:
            # 기본 로직: 간단한 키워드 체크
            insufficient_indicators = [
                "정확한 정보를 제공할 수 없다",
                "참고할 수 있는 문서가 없다",
                "문서에 없는 내용",
                "정보가 부족하다",
                "확실하지 않다"
            ]
            
            for indicator in insufficient_indicators:
                if indicator in rag_response:
                    return False
            
            # 길이 체크
            if len(rag_response.strip()) < 50:
                return False
                
            return True
    
    rag_quality_good = evaluate_rag_quality(rag_response, query)
    
    # 3. 최종 응답 선택
    if not rag_quality_good:
        # RAG 응답이 부족한 경우 LLM 사용 + 불확실성 표시
        llm = get_llm()
        llm_prompt = f"""다음은 관세 관련 질문입니다. 사전 학습된 지식만을 사용하여 답변해주세요.
        
질문: {query}

답변:"""
        
        llm_result = llm.invoke([HumanMessage(content=llm_prompt)])
        llm_response = str(llm_result.content) if hasattr(llm_result, 'content') else str(llm_result)
        
        # 불확실성 표시 추가
        final_response = f"{llm_response}\n\n※ 이 답변은 불확실할 수 있습니다."
        response_source = "LLM (RAG 응답 부족)"
        
    else:
        # RAG로 충분히 답변할 수 있는 경우 RAG만 사용
        final_response = rag_response
        response_source = "RAG (외부 지식 기반)"
    
    state["final_response"] = final_response
    state["intermediate_results"]["qna"] = {
        "rag_response": rag_response,
        "rag_quality_good": rag_quality_good,
        "selected_response": final_response,
        "response_source": response_source,
        "query": query
    }
    
    return state