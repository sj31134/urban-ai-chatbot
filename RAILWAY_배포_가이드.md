# 🚀 Railway 배포 가이드

## 📋 개요
이 가이드는 도시정비사업 법령 AI 챗봇을 Railway 플랫폼에 배포하는 전체 과정을 안내합니다.

## 🛠️ 배포 준비사항

### ✅ 현재 완료된 작업
- [x] Flask 웹 애플리케이션 구성
- [x] requirements.txt 최적화 (gunicorn 추가)
- [x] Procfile 생성 (Railway 실행 명령어)
- [x] railway.toml 설정 파일 생성
- [x] 환경변수 예시 파일 (env_example.txt)
- [x] 프로덕션 환경 대응 코드 수정

### 📦 배포 파일 구조
```
urban_legal_rag/
├── web_app.py              # Flask 웹 애플리케이션
├── requirements.txt        # Python 의존성
├── Procfile               # Railway 실행 명령어
├── railway.toml           # Railway 설정
├── env_example.txt        # 환경변수 예시
├── src/                   # 소스 코드
│   ├── rag/              # RAG 파이프라인
│   └── graph/            # Neo4j 그래프 매니저
└── templates/            # HTML 템플릿 (동적 생성)
```

## 🌐 Railway 배포 단계

### 1단계: Railway 계정 생성
1. [Railway 웹사이트](https://railway.app/) 접속
2. GitHub 계정으로 로그인
3. 새 프로젝트 생성

### 2단계: GitHub 저장소 연결
1. Railway 대시보드에서 "Deploy from GitHub repo" 선택
2. `sj31134/urban-ai-chatbot` 저장소 선택
3. 자동 배포 설정 활성화

### 3단계: 환경변수 설정
Railway 대시보드의 Variables 탭에서 다음 환경변수를 설정:

#### 🔑 필수 환경변수
```bash
# Neo4j 클라우드 데이터베이스
NEO4J_URI=neo4j+s://your-database-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

# Flask 애플리케이션
FLASK_ENV=production
FLASK_SECRET_KEY=your_very_secure_secret_key_here

# 프로토콜 버퍼 (호환성)
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# 로깅
LOG_LEVEL=INFO
```

#### 🔒 보안 주의사항
- `FLASK_SECRET_KEY`: 강력한 랜덤 키 생성 (32자 이상 권장)
- `NEO4J_PASSWORD`: Neo4j 클라우드 비밀번호
- Railway 환경변수는 자동으로 암호화되어 안전합니다

### 4단계: 배포 실행
1. 환경변수 설정 완료 후 "Deploy" 버튼 클릭
2. 빌드 로그 확인 (약 3-5분 소요)
3. 배포 완료 후 URL 확인

### 5단계: 배포 확인
1. Railway에서 제공한 도메인 접속
2. 웹 인터페이스 정상 작동 확인
3. 검색 기능 테스트

## 🎯 배포 후 검증

### ✅ 확인사항
- [ ] 웹페이지 로딩 정상
- [ ] Neo4j 데이터베이스 연결 성공
- [ ] 법령 검색 기능 작동
- [ ] 통계 정보 표시 정상
- [ ] 응답 시간 적절 (5초 이내)

### 🔍 테스트 질문 예시
- "도시정비사업이란 무엇인가요?"
- "조합설립인가 절차를 알려주세요"
- "주민동의 요건이 궁금해요"

## 🛡️ 보안 및 성능

### 🔐 보안 설정
- HTTPS 자동 적용 (Railway 제공)
- 환경변수 암호화
- CORS 설정 적용
- 프로덕션 모드 로깅

### ⚡ 성능 최적화
- Gunicorn WSGI 서버 사용
- 워커 프로세스 1개 (무료 티어 고려)
- 타임아웃 120초 설정
- 요청당 최대 1000개 제한

## 💰 비용 안내

### Railway 요금제
- **무료 티어**: 월 500 실행시간
- **Pro 플랜**: $5/월 (무제한 사용)
- **사용량 기반**: CPU/메모리 사용량에 따라

### 예상 비용
- 개발/테스트용: 무료 티어로 충분
- 실제 서비스용: Pro 플랜 권장

## 🔧 문제해결

### 자주 발생하는 오류
1. **빌드 실패**: requirements.txt 의존성 문제
   - 해결: Python 3.9 호환성 확인
   
2. **환경변수 오류**: Neo4j 연결 실패
   - 해결: URI, 사용자명, 비밀번호 재확인
   
3. **메모리 부족**: 임베딩 모델 로딩 실패
   - 해결: Pro 플랜으로 업그레이드

### 로그 확인 방법
1. Railway 대시보드 → Deployments
2. 최신 배포 클릭
3. Logs 탭에서 실시간 로그 확인

## 📞 지원 및 연락처

### 기술 지원
- GitHub Issues: [urban-ai-chatbot/issues](https://github.com/sj31134/urban-ai-chatbot/issues)
- Railway 문서: [docs.railway.app](https://docs.railway.app)

### 추가 기능 요청
새로운 기능이나 개선사항은 GitHub Issues에 등록해주세요.

---

## 🎉 배포 완료!

축하합니다! 도시정비사업 법령 AI 챗봇이 성공적으로 배포되었습니다.
이제 전 세계 어디서나 인터넷을 통해 접속할 수 있습니다.

**배포 URL**: `https://your-app-name.railway.app`

> 💡 **팁**: Railway는 커스텀 도메인도 지원합니다. 필요시 도메인 설정을 통해 더 전문적인 URL을 사용할 수 있습니다. 