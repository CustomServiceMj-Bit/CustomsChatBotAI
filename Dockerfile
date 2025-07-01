FROM python:3.11.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 코드 복사
COPY . .

# 환경변수 설정
ENV PYTHONUNBUFFERED=1

# 포트번호 명시
EXPOSE 5050

# Flask 앱 실행 (개발용 기준)
CMD ["python", "run.py"]