# 🚀 도시정비사업 법령 AI 챗봇 - 클라우드 배포 가이드

## 📋 배포 준비사항

### 필수 환경변수
다음 환경변수들을 클라우드 플랫폼에 설정해야 합니다:

```bash
# Neo4j 클라우드 데이터베이스
NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key

# LangSmith (선택사항)
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_TRACING_V2=true
```

## 🐳 Docker 로컬 테스트

### 1. 환경변수 파일 생성
```bash
# .env 파일 생성 (실제 값으로 교체)
cat > .env << 'EOF'
NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_api_key
LANGCHAIN_API_KEY=your_langchain_key
LANGCHAIN_TRACING_V2=true
EOF
```

### 2. Docker 이미지 빌드 및 실행
```bash
# 이미지 빌드
docker-compose build

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중단
docker-compose down
```

### 3. 접속 확인
- 로컬: http://localhost:8501
- 외부: http://your-server-ip:8501

## ☁️ 클라우드 플랫폼별 배포

### A. Railway 배포 (추천)

1. **Railway 프로젝트 생성**
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   ```

2. **환경변수 설정**
   ```bash
   railway variables set NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io
   railway variables set NEO4J_USERNAME=neo4j
   railway variables set NEO4J_PASSWORD=your_password
   railway variables set GOOGLE_API_KEY=your_api_key
   ```

3. **배포 실행**
   ```bash
   railway up
   ```

### B. Google Cloud Run

1. **gcloud CLI 설정**
   ```bash
   gcloud auth login
   gcloud config set project your-project-id
   ```

2. **이미지 빌드 및 푸시**
   ```bash
   docker build -t gcr.io/your-project-id/urban-ai-chatbot .
   docker push gcr.io/your-project-id/urban-ai-chatbot
   ```

3. **Cloud Run 배포**
   ```bash
   gcloud run deploy urban-ai-chatbot \
     --image gcr.io/your-project-id/urban-ai-chatbot \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --set-env-vars="NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io,NEO4J_USERNAME=neo4j,NEO4J_PASSWORD=your_password,GOOGLE_API_KEY=your_api_key"
   ```

### C. AWS ECS/Fargate

1. **ECR 레지스트리 생성**
   ```bash
   aws ecr create-repository --repository-name urban-ai-chatbot
   ```

2. **이미지 푸시**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   docker build -t urban-ai-chatbot .
   docker tag urban-ai-chatbot:latest your-account.dkr.ecr.us-east-1.amazonaws.com/urban-ai-chatbot:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/urban-ai-chatbot:latest
   ```

3. **ECS 태스크 정의 및 서비스 생성** (AWS Console 또는 CLI 사용)

### D. Streamlit Community Cloud

1. **GitHub 저장소 연결**
   - https://share.streamlit.io 접속
   - GitHub 저장소 연결
   - `src/chatbot/legal_assistant.py` 지정

2. **환경변수 설정**
   - Streamlit Cloud Settings에서 Secrets 설정:
   ```toml
   [secrets]
   NEO4J_URI = "neo4j+s://b51ef174.databases.neo4j.io"
   NEO4J_USERNAME = "neo4j"
   NEO4J_PASSWORD = "your_password"
   GOOGLE_API_KEY = "your_api_key"
   ```

## 🔧 배포 후 확인사항

### 1. 헬스체크
```bash
curl -f http://your-domain/_stcore/health
```

### 2. 기능 테스트
- [ ] Neo4j 연결 상태 확인
- [ ] Google Gemini API 연결 확인
- [ ] 법령 검색 기능 테스트
- [ ] 원문 파일 다운로드 테스트
- [ ] 관련 조문 추천 테스트

### 3. 로그 모니터링
```bash
# Docker 환경
docker-compose logs -f

# Cloud 환경은 각 플랫폼의 로그 서비스 이용
```

## 🚨 주의사항

1. **환경변수 보안**: API 키와 비밀번호는 반드시 환경변수로 관리
2. **리소스 제한**: 클라우드 플랫폼의 메모리/CPU 제한 확인
3. **네트워크**: Neo4j 클라우드와의 연결 가능한 리전 선택
4. **비용**: sentence-transformers 모델 다운로드로 인한 초기 로딩 시간 고려

## 📞 지원 및 문의

배포 중 문제 발생 시:
1. 로그 확인 및 오류 메시지 분석
2. 환경변수 설정 재확인
3. Neo4j/Gemini API 연결 상태 점검 