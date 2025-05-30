#!/bin/bash

# 도시정비 법령 Graph RAG 시스템 자동 설치 스크립트
# Author: Urban Legal RAG Team
# Version: 1.0

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 시작 메시지
echo "🏗️ =========================================="
echo "🏗️  도시정비 법령 Graph RAG 시스템 설치"
echo "🏗️ =========================================="
echo ""

# 1. 시스템 요구사항 확인
log_info "시스템 요구사항 확인 중..."

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION 감지됨"
else
    log_error "Python 3가 설치되지 않았습니다. Python 3.8 이상을 설치해주세요."
    exit 1
fi

# pip 확인
if ! command -v pip3 &> /dev/null; then
    log_error "pip3가 설치되지 않았습니다."
    exit 1
fi

# Docker 확인
if ! command -v docker &> /dev/null; then
    log_warning "Docker가 설치되지 않았습니다. Neo4j Docker 컨테이너를 사용할 수 없습니다."
    DOCKER_AVAILABLE=false
else
    log_success "Docker 감지됨"
    DOCKER_AVAILABLE=true
fi

# 2. 가상환경 생성 및 활성화
log_info "Python 가상환경 설정 중..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "가상환경 생성 완료"
else
    log_info "기존 가상환경 발견"
fi

# 가상환경 활성화
source venv/bin/activate
log_success "가상환경 활성화 완료"

# 3. Python 의존성 설치
log_info "Python 패키지 설치 중..."

# pip 업그레이드
pip install --upgrade pip

# 의존성 설치
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log_success "Python 패키지 설치 완료"
else
    log_error "requirements.txt 파일을 찾을 수 없습니다."
    exit 1
fi

# 4. 환경 변수 설정
log_info "환경 변수 설정 중..."

if [ -f "config/environment.env.template" ]; then
    if [ ! -f ".env" ]; then
        cp config/environment.env.template .env
        log_success "환경 변수 템플릿 복사 완료"
        log_warning "⚠️  .env 파일을 편집하여 API 키와 데이터베이스 설정을 입력해주세요!"
    else
        log_info "기존 .env 파일이 존재합니다."
    fi
else
    log_error "환경 변수 템플릿 파일을 찾을 수 없습니다."
fi

# 5. Neo4j 데이터베이스 설정
log_info "Neo4j 데이터베이스 설정 중..."

if [ "$DOCKER_AVAILABLE" = true ]; then
    # Docker로 Neo4j 설치
    log_info "Neo4j Docker 컨테이너 시작 중..."
    
    # 기존 컨테이너 확인
    if [ "$(docker ps -q -f name=neo4j-legal)" ]; then
        log_info "기존 Neo4j 컨테이너가 실행 중입니다."
    elif [ "$(docker ps -aq -f status=exited -f name=neo4j-legal)" ]; then
        log_info "중지된 Neo4j 컨테이너를 시작합니다."
        docker start neo4j-legal
    else
        log_info "새로운 Neo4j 컨테이너를 생성합니다."
        docker run -d \
            --name neo4j-legal \
            -p 7474:7474 \
            -p 7687:7687 \
            -v $(pwd)/data/neo4j:/data \
            -v $(pwd)/data/neo4j_logs:/logs \
            -e NEO4J_AUTH=legal_admin/secure_password \
            -e NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.* \
            -e NEO4J_dbms_security_procedures_allowlist=gds.*,apoc.* \
            neo4j:5.12
        
        log_success "Neo4j 컨테이너 생성 및 시작 완료"
    fi
    
    # Neo4j 시작 대기
    log_info "Neo4j 데이터베이스 시작을 기다리는 중..."
    sleep 30
    
    # 연결 테스트
    if curl -f http://localhost:7474 > /dev/null 2>&1; then
        log_success "Neo4j 데이터베이스 연결 확인"
        log_info "Neo4j 브라우저: http://localhost:7474"
        log_info "사용자명: legal_admin, 비밀번호: secure_password"
    else
        log_warning "Neo4j 연결을 확인할 수 없습니다. 수동으로 확인해주세요."
    fi
else
    log_warning "Docker를 사용할 수 없어 Neo4j를 수동으로 설치해야 합니다."
    log_info "Neo4j 다운로드: https://neo4j.com/download/"
fi

# 6. 로그 디렉토리 생성
log_info "로그 디렉토리 생성 중..."
mkdir -p logs
log_success "로그 디렉토리 생성 완료"

# 7. 샘플 데이터 준비
log_info "샘플 데이터 디렉토리 확인 중..."

# 데이터 디렉토리가 비어있다면 안내 메시지 출력
if [ -z "$(ls -A data/laws 2>/dev/null)" ]; then
    log_warning "법령 데이터가 없습니다."
    log_info "다음 위치에 법령 PDF 파일을 배치해주세요:"
    log_info "  - data/laws/ (도시정비법, 소규모주택정비법 등)"
    log_info "  - data/ordinances/ (지자체 조례)"
fi

# 8. 그래프 스키마 초기화
log_info "Neo4j 그래프 스키마 초기화 중..."

# Neo4j가 준비될 때까지 대기
if [ "$DOCKER_AVAILABLE" = true ]; then
    sleep 10
    
    # 스키마 초기화 스크립트 실행
    if python3 -c "
from src.graph.legal_graph import LegalGraphManager
try:
    manager = LegalGraphManager()
    manager.initialize_schema()
    manager.close()
    print('스키마 초기화 성공')
except Exception as e:
    print(f'스키마 초기화 실패: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "그래프 스키마 초기화 완료"
    else
        log_warning "그래프 스키마 초기화에 실패했습니다. 수동으로 실행해주세요."
    fi
fi

# 9. Streamlit 앱 설정
log_info "Streamlit 웹 앱 설정 중..."

# Streamlit 설정 디렉토리 생성
mkdir -p .streamlit

# Streamlit 설정 파일 생성
cat > .streamlit/config.toml << EOF
[global]
dataFrameSerialization = "legacy"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#3B82F6"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8FAFC"
textColor = "#1F2937"
font = "sans serif"
EOF

log_success "Streamlit 설정 완료"

# 10. 실행 스크립트 생성
log_info "실행 스크립트 생성 중..."

# 시스템 시작 스크립트
cat > start_system.sh << 'EOF'
#!/bin/bash

echo "🏗️ 도시정비 법령 RAG 시스템 시작"
echo "=================================="

# 가상환경 활성화
source venv/bin/activate

# Neo4j 컨테이너 시작 (Docker 사용 시)
if command -v docker &> /dev/null; then
    if [ "$(docker ps -q -f name=neo4j-legal)" ]; then
        echo "✅ Neo4j 컨테이너가 이미 실행 중입니다."
    else
        echo "🔄 Neo4j 컨테이너를 시작합니다..."
        docker start neo4j-legal
        sleep 10
    fi
fi

# Streamlit 앱 시작
echo "🚀 Streamlit 웹 앱을 시작합니다..."
echo "📱 브라우저에서 http://localhost:8501 에 접속하세요"
echo ""

streamlit run src/chatbot/legal_assistant.py
EOF

# 시스템 중지 스크립트
cat > stop_system.sh << 'EOF'
#!/bin/bash

echo "🛑 도시정비 법령 RAG 시스템 종료"
echo "================================"

# Streamlit 프로세스 종료
if pgrep -f "streamlit" > /dev/null; then
    echo "🔄 Streamlit 프로세스를 종료합니다..."
    pkill -f "streamlit"
fi

# Neo4j 컨테이너 중지 (Docker 사용 시)
if command -v docker &> /dev/null; then
    if [ "$(docker ps -q -f name=neo4j-legal)" ]; then
        echo "🔄 Neo4j 컨테이너를 중지합니다..."
        docker stop neo4j-legal
    fi
fi

echo "✅ 시스템 종료 완료"
EOF

# 스크립트 실행 권한 부여
chmod +x start_system.sh
chmod +x stop_system.sh

log_success "실행 스크립트 생성 완료"

# 11. 테스트 실행 (선택사항)
read -p "🧪 테스트를 실행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "테스트 실행 중..."
    
    if python3 -m pytest tests/ -v --tb=short; then
        log_success "모든 테스트가 통과했습니다!"
    else
        log_warning "일부 테스트가 실패했습니다. 로그를 확인해주세요."
    fi
fi

# 12. 설치 완료 메시지
echo ""
echo "🎉 =========================================="
echo "🎉  도시정비 법령 RAG 시스템 설치 완료!"
echo "🎉 =========================================="
echo ""
log_success "설치가 성공적으로 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "  1. .env 파일을 편집하여 API 키를 설정하세요"
echo "  2. data/laws/ 디렉토리에 법령 PDF 파일을 배치하세요"
echo "  3. ./start_system.sh 로 시스템을 시작하세요"
echo ""
echo "🔗 유용한 링크:"
echo "  • 시스템 시작: ./start_system.sh"
echo "  • 시스템 중지: ./stop_system.sh"
echo "  • 웹 인터페이스: http://localhost:8501"
echo "  • Neo4j 브라우저: http://localhost:7474"
echo ""
echo "📚 문서:"
echo "  • README.md: 프로젝트 개요 및 사용법"
echo "  • config/: 설정 파일들"
echo "  • tests/: 테스트 코드"
echo ""
log_info "설치 로그는 logs/ 디렉토리에서 확인할 수 있습니다."

# 마지막 안내사항
echo ""
log_warning "⚠️  중요 안내사항:"
echo "  • Google Gemini API 키가 필요합니다"
echo "  • Neo4j 데이터베이스 연결을 확인하세요"
echo "  • 법령 데이터 수집 시 저작권을 준수하세요"
echo "" 