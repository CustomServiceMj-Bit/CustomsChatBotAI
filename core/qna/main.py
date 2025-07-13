import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
from core.qna.retriever import RAGRetriever
from core.qna.generator import AnswerGenerator
from core.qna.database import ChromaDBManager


class RAGSystem:
    def __init__(self):
        self.retriever = RAGRetriever()
        self.generator = AnswerGenerator()
        
    def setup_database(self):
        """Initialize database with data from pickle files"""
        self.retriever.db_manager.setup_database()
        
    def search_and_generate(self, query, top_k=5, show_details=False):
        """
        Complete RAG pipeline: search + generate
        
        Args:
            query: str - user question
            top_k: int - number of documents to retrieve
            show_details: bool - whether to show retrieval details
            
        Returns:
            str: final generated answer
        """
        # Retrieve relevant documents
        results = self.retriever.search_with_weights(query, top_k=top_k)
        
        # if show_details:
        #     print("=== 검색 결과 ===")
        #     for r in results:
        #         print(f"[{r['index']}] {r['question']}")
        #         print(f"→ {r['answer']}")
        #         print(f"Entities: {r['entities']}")
        #         print(f"Scores → Q: {r['score_question']:.4f} / A: {r['score_snippet']:.4f} / E: {r['score_keyword']:.4f} / Total: {r['score_combined']:.4f}")
        #         print("-" * 50)
        
        # Generate answer
        prompt = self.generator.build_prompt(query, results)
        final_answer = self.generator.generate_answer(prompt)
        
        return final_answer


def main():
    parser = argparse.ArgumentParser(description='RAG 시스템을 사용하여 관세 관련 질문에 답변합니다.')
    parser.add_argument('--query', '-q', type=str, required=True, help='질문을 입력하세요')
    parser.add_argument('--top_k', '-k', type=int, default=5, help='검색할 문서 수 (기본값: 5)')
    parser.add_argument('--setup', action='store_true', help='데이터베이스 초기 설정 실행')
    parser.add_argument('--show_details', '-d', action='store_true', help='검색 결과 상세정보 표시')
    
    args = parser.parse_args()
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    # Setup database if requested
    if args.setup:
        # print("데이터베이스를 설정하고 있습니다...")
        rag_system.setup_database()
        # print("데이터베이스 설정이 완료되었습니다!")
    
    # Get answer
    # print(f"질문: {args.query}")
    # print("답변을 생성하고 있습니다...\n")
    
    answer = rag_system.search_and_generate(
        args.query, 
        top_k=args.top_k, 
        show_details=args.show_details
    )
    print(answer)
""" 최종 반환 답변 타입은 단순한 텍스트입니다. """
""" String 타입으로, 생성된 답변만 출력합니다."""