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
