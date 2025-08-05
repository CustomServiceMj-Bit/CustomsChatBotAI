"""
Answer generation using OpenAI GPT models
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from core.qna.config import OPENAI_MODEL, GENERATION_TEMPERATURE, MAX_REFERENCE_DOCS

load_dotenv()


class AnswerGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def build_prompt(self, query, retrieved_docs, max_docs=MAX_REFERENCE_DOCS):
        """
        Build prompt for answer generation
        
        Args:
            query: str - user question
            retrieved_docs: list - retrieved documents from RAG
            max_docs: int - maximum number of documents to include
            
        Returns:
            str: formatted prompt
        """
        prompt = f"""당신은 관세 전문가입니다. 사용자의 질문에 대해 아래 문서를 참고하여 정확하게 답변하세요.

질문: "{query}"

다음은 참고할 수 있는 문서입니다:
"""
        for i, doc in enumerate(retrieved_docs[:max_docs]):
            prompt += f"\n문서 {i+1}:\n질문: {doc['question']}\n답변: {doc['answer']}\n"
            
        prompt += """
위 문서를 참고하여 사용자의 질문에 대해 정리된 답변을 제공하세요. 

중요한 지침:
1. 반드시 참고 문서에 근거하여 설명하고, 문서에 없는 내용을 임의로 생성하지 마세요.
2. 답변 중간에 [1], [2] 같은 출처 표시를 사용하지 마세요.
3. 답변 내용을 먼저 완성한 후, 마지막에 "참고 문서:" 또는 "출처:"라는 제목으로 어떤 문서들을 참고했는지 한 번에 명시하세요.
4. 문서를 바탕으로 답변하지 못하는 경우, 정확한 정보를 제공할 수 없다고 답변하세요.

답변 형식:
[답변 내용]

참고 문서:
- 문서 1: [간단한 설명]
- 문서 2: [간단한 설명]
...
"""
        return prompt
        
    def generate_answer(self, prompt):
        """
        Generate answer using OpenAI GPT
        
        Args:
            prompt: str - formatted prompt
            
        Returns:
            str: generated answer
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "관세 전문가로서 질문에 답해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=GENERATION_TEMPERATURE
        )
        return response.choices[0].message.content.strip()