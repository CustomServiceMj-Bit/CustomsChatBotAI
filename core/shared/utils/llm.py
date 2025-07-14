from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

def get_llm():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수 또는 .env 파일에 키가 필요합니다.")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)