import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
from core.qna.retriever import RAGRetriever
from core.qna.generator import AnswerGenerator


class RAGSystem:
    def __init__(self):
        self.retriever = RAGRetriever()
        self.generator = AnswerGenerator()
        
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
        
        # Generate answer
        prompt = self.generator.build_prompt(query, results)
        final_answer = self.generator.generate_answer(prompt)
        
        return final_answer


def main():
    parser = argparse.ArgumentParser(description='RAG 시스템을 사용하여 관세 관련 질문에 답변합니다.')
    parser.add_argument('--query', '-q', type=str, required=True, help='질문을 입력하세요')
    parser.add_argument('--top_k', '-k', type=int, default=5, help='검색할 문서 수 (기본값: 5)')
    parser.add_argument('--show_details', '-d', action='store_true', help='검색 결과 상세정보 표시')
    
    args = parser.parse_args()
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    # Get answer
    answer = rag_system.search_and_generate(
        args.query, 
        top_k=args.top_k, 
        show_details=args.show_details
    )
    print(answer)


if __name__ == "__main__":
    main()