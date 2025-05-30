#!/bin/bash

echo "🛑 도시정비 법령 RAG 시스템 종료"
echo "================================"

# Streamlit 프로세스 종료
if pgrep -f "streamlit" > /dev/null; then
    echo "🔄 Streamlit 프로세스를 종료합니다..."
    pkill -f "streamlit"
    echo "✅ Streamlit 프로세스 종료 완료"
else
    echo "ℹ️  실행 중인 Streamlit 프로세스가 없습니다."
fi

# Neo4j 컨테이너 중지 (Docker 사용 시)
if command -v docker &> /dev/null; then
    if [ "$(docker ps -q -f name=neo4j-legal)" ]; then
        echo "🔄 Neo4j 컨테이너를 중지합니다..."
        docker stop neo4j-legal
        echo "✅ Neo4j 컨테이너 중지 완료"
    else
        echo "ℹ️  실행 중인 Neo4j 컨테이너가 없습니다."
    fi
else
    echo "⚠️  Docker가 설치되지 않았습니다. Neo4j를 수동으로 중지해주세요."
fi

echo "✅ 시스템 종료 완료" 