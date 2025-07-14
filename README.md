# CustomServiceAI

## 실행 방법 (Docker Compose)

이 프로젝트는 Docker Compose로 쉽게 실행할 수 있습니다.

### ✅ 사전 조건
- [Docker](https://www.docker.com/) 설치
- [Docker Compose](https://docs.docker.com/compose/install/) 설치
- `.env` 파일에 필요한 환경 변수 설정 (한국수출입은행, 유니패스, GPT api 경로 및 키 설정 필요)

### 🚀 실행 방법

```bash
docker compose up -d
```

→ **테스트**: 실행 후 브라우저에서 [http://localhost:5050/apidocs](http://localhost:5050/apidocs) 접속

### 🛑 종료 방법

```bash
docker compose down
```

## 📊 데이터베이스 설정

### VectorDB 사용
이 프로젝트는 기존 VectorDB의 pickle 파일들을 직접 사용합니다:
- `core/qna/VectorDB/q_data.pkl`: 질문 임베딩 데이터
- `core/qna/VectorDB/s_data.pkl`: 답변 스니펫 임베딩 데이터  
- `core/qna/VectorDB/k_data.pkl`: 키워드 임베딩 데이터

**장점**:
- ChromaDB 없이도 동작
- 빠른 로딩 속도
- Git 저장소 크기 최적화
- 간단한 구조
