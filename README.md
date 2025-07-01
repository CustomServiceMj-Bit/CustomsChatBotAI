# CustomServiceAI

## 실행 방법 (Docker Compose)

이 프로젝트는 Docker Compose로 쉽게 실행할 수 있습니다.

### ✅ 사전 조건
- [Docker](https://www.docker.com/) 설치
- [Docker Compose](https://docs.docker.com/compose/install/) 설치
- `.env` 파일에 필요한 환경 변수 설정 (옵션)

### 🚀 실행 방법

```bash
docker compose up -d
```

→ 테스트: 실행 후 브라우저에서 [http://localhost:5050/apidocs](http://localhost:5050/apidocs) 접속

### 🛑 종료 방법

```bash
docker compose down
```