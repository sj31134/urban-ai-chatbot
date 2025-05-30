#!/bin/bash

echo "🏗️ 도시정비 법령 RAG 시스템 시작"
echo "=================================="

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "🔄 가상환경 활성화 중..."
    source venv/bin/activate
    echo "✅ 가상환경 활성화 완료"
else
    echo "⚠️  가상환경이 없습니다. setup_legal_rag.sh를 먼저 실행해주세요."
    exit 1
fi

# Neo4j 컨테이너 시작 (Docker 사용 시)
if command -v docker &> /dev/null; then
    if [ "$(docker ps -q -f name=neo4j-legal)" ]; then
        echo "✅ Neo4j 컨테이너가 이미 실행 중입니다."
    else
        echo "🔄 Neo4j 컨테이너를 시작합니다..."
        docker start neo4j-legal || {
            echo "⚠️  Neo4j 컨테이너를 찾을 수 없습니다. setup_legal_rag.sh를 먼저 실행해주세요."
        }
        sleep 10
    fi
else
    echo "⚠️  Docker가 설치되지 않았습니다. Neo4j를 수동으로 시작해주세요."
fi

# 환경변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.sample을 참고하여 .env 파일을 생성해주세요."
    exit 1
fi

# Streamlit 앱 시작
echo "🚀 Streamlit 웹 앱을 시작합니다..."
echo "📱 브라우저에서 http://localhost:8501 에 접속하세요"
echo ""

streamlit run src/chatbot/legal_assistant.py 