# 도시정비사업 법령 AI 챗봇 - 클라우드 배포용 Dockerfile
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

# 포트 설정 (Streamlit 기본 포트)
EXPOSE 8501

# 환경변수 설정
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 헬스체크 설정
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit 앱 실행
CMD ["streamlit", "run", "src/chatbot/legal_assistant.py", "--server.port=8501", "--server.address=0.0.0.0"] 