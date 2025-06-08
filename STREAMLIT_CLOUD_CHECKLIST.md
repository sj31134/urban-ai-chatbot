# 🚀 Streamlit Community Cloud 배포 체크리스트

## ✅ 코드 준비 상태

### 1. 환경변수 호환성
- [x] `st.secrets` 지원 코드 추가
- [x] `os.getenv()` 백업 처리
- [x] 모든 주요 모듈에 적용 완료

### 2. 패키지 최적화
- [x] `requirements.txt` Streamlit 활성화
- [x] Flask 의존성 주석처리 (불필요)
- [x] 메모리 최적화 (`device='cpu'`)

### 3. 코드 검증
- [x] Python 구문 검사 통과
- [x] 주요 패키지 import 테스트 통과
- [x] 환경변수 처리 함수 테스트 통과

## 📋 배포 단계

### 1단계: GitHub 저장소 확인
- [ ] 최신 코드 커밋 & 푸시
- [ ] 브랜치가 `main`인지 확인
- [ ] `src/chatbot/legal_assistant.py` 존재 확인

### 2단계: Streamlit Community Cloud 접속
- [ ] https://share.streamlit.io 방문
- [ ] GitHub 계정으로 로그인
- [ ] "Create app" 클릭

### 3단계: 앱 설정
```
Repository: sj31134/urban-ai-chatbot
Branch: main
Main file path: src/chatbot/legal_assistant.py
```

### 4단계: Secrets 설정
```toml
# App settings에서 Secrets 탭 선택하여 입력

NEO4J_URI = "neo4j+s://b51ef174.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_neo4j_password"
GOOGLE_API_KEY = "your_google_api_key"

# 선택사항
LANGCHAIN_API_KEY = "your_langchain_api_key"
LANGCHAIN_TRACING_V2 = "true"
```

## ⚠️ 알려진 제한사항

### 메모리 제한 (1GB)
- **현재 상태**: sentence-transformers 모델이 메모리 집약적
- **대응책**: CPU 모드, 캐시 최적화 적용됨
- **모니터링**: 배포 후 메모리 사용량 관찰 필요

### 콜드 스타트
- **예상 시간**: 첫 로딩 30-60초
- **원인**: 임베딩 모델 다운로드
- **사용자 안내**: 로딩 메시지 표시됨

## 🔧 문제해결 가이드

### 메모리 초과 오류
```
RuntimeError: CUDA out of memory
```
**해결책**: 이미 `device='cpu'` 설정 완료

### Neo4j 연결 실패
```
Neo4j connection failed
```
**해결책**: Secrets에서 NEO4J_* 환경변수 확인

### API 키 오류
```
Google API key not found
```
**해결책**: Secrets에서 GOOGLE_API_KEY 확인

## 🚀 배포 후 확인사항

### 기능 테스트
- [ ] 페이지 로딩 확인
- [ ] 질의 입력 테스트
- [ ] Neo4j 연결 상태 확인
- [ ] 출처 조문 표시 확인
- [ ] 관련 조문 추천 확인

### 성능 모니터링
- [ ] 첫 응답 시간 측정
- [ ] 메모리 사용량 확인
- [ ] 오류 로그 점검

## 📞 지원 리소스

- **Streamlit 문서**: https://docs.streamlit.io/streamlit-community-cloud
- **GitHub 저장소**: https://github.com/sj31134/urban-ai-chatbot
- **Neo4j Aura**: https://console.neo4j.io/
- **Google AI Studio**: https://makersuite.google.com/ 

# Homebrew를 통한 Docker 설치
brew install --cask docker 

docker-compose up -d neo4j 