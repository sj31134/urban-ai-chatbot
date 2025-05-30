#!/bin/bash

# 도시정비사업 AI 챗봇 Git 저장소 설정 스크립트
# Author: sj31134
# Repository: urban-ai-chatbot

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔧 ========================================"
echo "🔧  Git 저장소 초기화 및 GitHub 연결"
echo "🔧 ========================================"
echo ""

# GitHub Personal Access Token 설정
GITHUB_TOKEN="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"
GITHUB_USERNAME="sj31134"
REPO_NAME="urban-ai-chatbot"

# 1. Git 사용자 정보 설정
log_info "Git 사용자 정보 설정 중..."
git config --global user.name "sj31134"
git config --global user.email "sj31134@gmail.com"
log_success "Git 사용자 정보 설정 완료"

# 2. Git 저장소 초기화 (이미 초기화되어 있지 않은 경우)
if [ ! -d ".git" ]; then
    log_info "Git 저장소 초기화 중..."
    git init
    log_success "Git 저장소 초기화 완료"
else
    log_info "Git 저장소가 이미 초기화되어 있습니다."
fi

# 3. 환경변수 파일 복사 (실제 .env 파일 생성)
if [ ! -f ".env" ]; then
    log_info ".env 파일 생성 중..."
    cp config/environment.env.template .env
    log_success ".env 파일 생성 완료"
    log_warning "⚠️  .env 파일에 실제 API 키를 입력해주세요!"
else
    log_info ".env 파일이 이미 존재합니다."
fi

# 4. 기본 브랜치를 main으로 설정
log_info "기본 브랜치를 main으로 설정 중..."
git branch -M main
log_success "기본 브랜치 설정 완료"

# 5. GitHub Personal Access Token을 사용한 credential 설정
log_info "GitHub 인증 설정 중..."
git config --global credential.helper store
echo "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
log_success "GitHub 인증 설정 완료"

# 6. GitHub 원격 저장소 추가
log_info "GitHub 원격 저장소 연결 중..."
if git remote get-url origin > /dev/null 2>&1; then
    log_info "원격 저장소가 이미 설정되어 있습니다."
    git remote set-url origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git
    log_success "원격 저장소 URL 업데이트 완료"
    git remote -v
else
    git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git
    log_success "GitHub 원격 저장소 연결 완료"
fi

# 7. GitHub 저장소 존재 여부 확인 및 생성
log_info "GitHub 저장소 확인 중..."
if curl -f -H "Authorization: token ${GITHUB_TOKEN}" \
   "https://api.github.com/repos/${GITHUB_USERNAME}/${REPO_NAME}" > /dev/null 2>&1; then
    log_success "GitHub 저장소가 이미 존재합니다."
else
    log_info "GitHub 저장소를 생성합니다..."
    curl -H "Authorization: token ${GITHUB_TOKEN}" \
         -H "Content-Type: application/json" \
         -d "{
           \"name\": \"${REPO_NAME}\",
           \"description\": \"도시정비사업 법령 전문 AI 챗봇 - Neo4j Graph RAG + LangChain + Gemini\",
           \"private\": true,
           \"has_issues\": true,
           \"has_projects\": true,
           \"has_wiki\": false
         }" \
         "https://api.github.com/user/repos"
    
    if [ $? -eq 0 ]; then
        log_success "GitHub 저장소 생성 완료"
    else
        log_error "GitHub 저장소 생성 실패. 수동으로 생성해주세요."
    fi
fi

# 8. 공개용 환경변수 샘플 파일 생성
log_info "공개용 환경변수 샘플 파일 생성 중..."
cat > .env.sample << 'EOF'
# 도시정비사업 Graph RAG 시스템 환경변수 (샘플)
# 실제 사용 시 .env 파일로 복사하여 사용하세요

# Neo4j 그래프 데이터베이스 설정
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=legal_admin
NEO4J_PASSWORD=your_secure_password_here
NEO4J_DATABASE=legal_graph

# Google Gemini API 설정 (필수)
GOOGLE_API_KEY=your_gemini_api_key_here

# LangChain 설정 (선택사항)
LANGCHAIN_PROJECT=urban_legal_rag
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key_here

# 임베딩 모델 설정
EMBEDDING_MODEL=bge-m3
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# 법령 데이터 소스 URL
MOLEG_BASE_URL=https://www.law.go.kr
MOLIT_BASE_URL=http://www.molit.go.kr
SEOUL_LEGAL_URL=https://legal.seoul.go.kr
BUSAN_LEGAL_URL=https://council.busan.go.kr

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=logs/legal_rag.log

# 보안 설정
SECRET_KEY=your_secret_key_for_encryption
ALLOWED_HOSTS=localhost,127.0.0.1

# 성능 설정
MAX_WORKERS=4
TIMEOUT_SECONDS=30
CACHE_TTL=3600
EOF
log_success "환경변수 샘플 파일 생성 완료"

# 9. 초기 커밋 준비
log_info "초기 커밋 준비 중..."

# .gitignore가 제대로 적용되도록 캐시 정리
git rm -r --cached . > /dev/null 2>&1 || true

# 파일 추가 (민감한 파일 제외)
git add .gitignore
git add README.md
git add LICENSE
git add requirements.txt
git add .env.sample
git add setup_legal_rag.sh
git add start_system.sh
git add stop_system.sh
git add git_setup.sh
git add config/
git add src/
git add tests/
git add .github/
git add .streamlit/ > /dev/null 2>&1 || true

log_success "파일 스테이징 완료"

# 10. 초기 커밋
log_info "초기 커밋 생성 중..."
if git diff --cached --quiet; then
    log_warning "커밋할 변경사항이 없습니다."
else
    git commit -m "feat: 도시정비사업 Graph RAG 시스템 초기 설정 완료

- Neo4j Graph RAG 아키텍처 구축  
- LangChain + Google Gemini 통합
- Streamlit 웹 인터페이스 구현
- 도시정비법/소규모주택정비법 지원
- GitHub Actions CI/CD 파이프라인
- 종합 테스트 케이스 구축
- Personal Access Token 인증 설정"
    
    log_success "초기 커밋 생성 완료"
fi

# 11. main 브랜치 푸시
log_info "main 브랜치 푸시 중..."
if git push -u origin main; then
    log_success "main 브랜치 푸시 완료"
else
    log_error "main 브랜치 푸시 실패. 네트워크나 권한을 확인해주세요."
fi

# 12. develop 브랜치 생성 및 푸시
log_info "develop 브랜치 생성 중..."
git checkout -b develop
if git push -u origin develop; then
    log_success "develop 브랜치 생성 및 푸시 완료"
else
    log_warning "develop 브랜치 푸시 실패. 나중에 다시 시도해주세요."
fi

# main 브랜치로 돌아가기
git checkout main

echo ""
echo "🎉 =========================================="
echo "🎉  Git 저장소 설정 완료!"
echo "🎉 =========================================="
echo ""
log_success "GitHub 저장소가 성공적으로 설정되었습니다!"
echo ""
echo "🔗 유용한 링크:"
echo "  • GitHub 저장소: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo "  • Issues: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/issues"
echo "  • Actions: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
echo "  • Settings: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/settings"
echo ""
echo "📋 다음 단계:"
echo "  1. GitHub 저장소에서 업로드된 파일 확인"
echo "  2. .env 파일에 실제 API 키 입력"
echo "  3. GitHub Secrets 설정:"
echo "     - GOOGLE_API_KEY: Gemini API 키"
echo "  4. 브랜치 보호 규칙 설정 (Settings → Branches)"
echo ""
log_warning "⚠️  중요 보안 사항:"
log_info "  • .env 파일은 절대 커밋되지 않습니다"
log_info "  • Personal Access Token은 안전하게 보관하세요"
log_info "  • .env.sample 파일만 공개 저장소에 포함됩니다"

# 인증 정보 정리 (보안)
log_info "임시 인증 정보 정리 중..."
rm -f ~/.git-credentials
log_success "보안 정리 완료" 