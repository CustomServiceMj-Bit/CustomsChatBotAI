#!/usr/bin/env python3
"""
간단한 테스트 - 질문하고 답변 받기
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple_qa():
    """간단한 질문-답변 테스트"""
    try:
        from core.qna.main import RAGSystem
        
        # RAG 시스템 초기화
        rag_system = RAGSystem()
        
        # 테스트 질문
        question = "수입 신고는 어떻게 하나요?"
        print(f"질문: {question}")
        print("-" * 50)
        
        # 답변 생성
        answer = rag_system.search_and_generate(question)
        print(f"답변: {answer}")
        
        print("\n✅ 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_simple_qa() 