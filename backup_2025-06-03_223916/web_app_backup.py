#!/usr/bin/env python3
"""
도시정비사업 법령 전문 AI 챗봇 - 조문 클릭 팝업 기능 추가
"""

import sys
import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'urban_legal_rag_enhanced_secret_key_2024'
CORS(app)

# 전역 변수로 RAG 시스템 인스턴스 관리
graph_manager = None
rag_pipeline = None
is_initialized = False


def initialize_system():
    """시스템 초기화"""
    global graph_manager, rag_pipeline, is_initialized
    
    if is_initialized:
        return True
    
    try:
        print("🤖 도시정비사업 법령 전문 AI 챗봇 웹 서버 초기화 중...")
        
        # 그래프 관리자 초기화
        print("   🔗 Neo4j 데이터베이스 연결 중...")
        graph_manager = LegalGraphManager()
        
        # RAG 파이프라인 초기화
        print("   🧠 RAG 검색 시스템 초기화 중...")
        rag_pipeline = EnhancedRAGPipeline(graph_manager)
        
        print("✅ 시스템 초기화 완료!")
        
        # 시스템 통계 출력
        stats = rag_pipeline.get_system_stats()
        print(f"   📄 법령 데이터: {stats['graph_stats'].get('Law', 0)}개 법령, {stats['graph_stats'].get('Article', 0)}개 조문")
        print(f"   🧠 임베딩: {stats['embedding_stats']['total_chunks']}개 청크")
        
        is_initialized = True
        return True
        
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        return False


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index_enhanced.html')


@app.route('/api/search', methods=['POST'])
def search():
    """검색 API"""
    global rag_pipeline
    
    try:
        if not is_initialized:
            return jsonify({'error': '시스템이 초기화되지 않았습니다.'}), 500
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400
        
        # 세션 정보 업데이트
        if 'start_time' not in session:
            session['start_time'] = datetime.now().isoformat()
        session['query_count'] = session.get('query_count', 0) + 1
        
        # 검색 수행
        start_time = time.time()
        results = rag_pipeline.search(query, search_type="hybrid", k=3)
        search_time = round(time.time() - start_time, 3)
        
        # 결과 포맷팅
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = {
                "rank": i,
                "article_number": result.get("article_number", "N/A"),
                "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "full_content": result.get("content", ""),  # 팝업용 전체 내용
                "law_name": result.get("law_name", "N/A"),
                "law_id": result.get("law_id", "N/A"),  # 팝업용 법령 ID
                "section": result.get("section", ""),
                "score": result.get("score", 0),
                "confidence": get_confidence_level(result.get("score", 0))
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            "query": query,
            "results": formatted_results,
            "search_time": f"{search_time}초",
            "result_count": len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'검색 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/article/detail', methods=['POST'])
def get_article_detail():
    """조문 상세 조회 API - 새로 추가된 기능!"""
    global graph_manager
    
    try:
        if not is_initialized:
            return jsonify({'error': '시스템이 초기화되지 않았습니다.'}), 500
        
        data = request.get_json()
        article_number = data.get('article_number', '').strip()
        law_id = data.get('law_id', '').strip()
        
        if not article_number:
            return jsonify({'error': '조문 번호가 필요합니다.'}), 400
        
        # 조문 상세 정보 조회
        article_detail = get_article_detailed_info(article_number, law_id)
        
        if not article_detail:
            return jsonify({'error': '조문을 찾을 수 없습니다.'}), 404
        
        return jsonify(article_detail)
        
    except Exception as e:
        return jsonify({'error': f'조문 조회 중 오류가 발생했습니다: {str(e)}'}), 500


def get_article_detailed_info(article_number: str, law_id: str = None) -> dict:
    """조문 상세 정보 조회"""
    global graph_manager
    
    try:
        with graph_manager.driver.session() as session:
            # 기본 조문 정보 조회
            if law_id and law_id != "N/A":
                query = """
                MATCH (a:Article {article_number: $article_number, law_id: $law_id})-[:BELONGS_TO]->(l:Law)
                RETURN a.article_number as article_number,
                       a.content as content,
                       a.section as section,
                       a.subsection as subsection,
                       l.name as law_name,
                       l.law_id as law_id,
                       l.category as category,
                       id(a) as node_id
                """
                params = {"article_number": article_number, "law_id": law_id}
            else:
                query = """
                MATCH (a:Article {article_number: $article_number})-[:BELONGS_TO]->(l:Law)
                RETURN a.article_number as article_number,
                       a.content as content,
                       a.section as section,
                       a.subsection as subsection,
                       l.name as law_name,
                       l.law_id as law_id,
                       l.category as category,
                       id(a) as node_id
                LIMIT 1
                """
                params = {"article_number": article_number}
            
            result = session.run(query, params)
            article_data = result.single()
            
            if not article_data:
                return None
            
            article_info = dict(article_data)
            
            # 관련 조문 조회 (같은 법령의 다른 조문들)
            related_query = """
            MATCH (a:Article)-[:BELONGS_TO]->(l:Law {law_id: $law_id})
            WHERE a.article_number <> $article_number
            RETURN a.article_number as article_number,
                   a.content as content,
                   a.section as section
            ORDER BY a.article_number
            LIMIT 5
            """
            
            related_result = session.run(related_query, {
                "law_id": article_info["law_id"],
                "article_number": article_number
            })
            
            related_articles = [dict(record) for record in related_result]
            
            # 교차 참조 조회
            cross_refs = graph_manager.find_cross_references(article_info["content"])
            
            return {
                "article": article_info,
                "related_articles": related_articles,
                "cross_references": cross_refs[:3],  # 최대 3개
                "total_related": len(related_articles)
            }
            
    except Exception as e:
        print(f"조문 상세 조회 오류: {e}")
        return None


@app.route('/api/stats')
def get_stats():
    """시스템 통계 API"""
    global rag_pipeline
    
    try:
        if not is_initialized:
            return jsonify({'error': '시스템이 초기화되지 않았습니다.'}), 500
        
        stats = rag_pipeline.get_system_stats()
        
        # 세션 정보 추가
        session_start = session.get('start_time')
        if session_start:
            session_start_dt = datetime.fromisoformat(session_start)
            session_duration = str(datetime.now() - session_start_dt).split('.')[0]
        else:
            session_duration = "00:00:00"
        
        return jsonify({
            'system_stats': stats,
            'session_stats': {
                'query_count': session.get('query_count', 0),
                'session_duration': session_duration
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'통계 조회 오류: {str(e)}'}), 500


def get_confidence_level(score):
    """신뢰도 레벨 계산"""
    if score >= 0.8:
        return "매우 높음"
    elif score >= 0.6:
        return "높음"
    elif score >= 0.4:
        return "보통"
    else:
        return "낮음"


# HTML 템플릿 생성 (팝업 모달 기능 추가)
def create_templates():
    """HTML 템플릿 파일들 생성"""
    
    # templates 디렉토리 생성
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # index_enhanced.html 생성 (팝업 기능 포함)
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>도시정비사업 법령 전문 AI 챗봇 - 향상된 버전</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #4a5568;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .header p {
            color: #718096;
            font-size: 1.2em;
        }
        
        .stats-panel {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .chat-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            min-height: 600px;
            display: flex;
            flex-direction: column;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            max-height: 500px;
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            max-width: 85%;
        }
        
        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .bot-message {
            background: white;
            border: 1px solid #e2e8f0;
            margin-right: auto;
        }
        
        .search-result {
            background: #f0f8ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        
        .result-header {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;  /* 클릭 가능 표시 */
            transition: all 0.3s ease;
        }
        
        .result-header:hover {
            background: rgba(102, 126, 234, 0.1);  /* 호버 효과 */
            border-radius: 5px;
            padding: 5px;
            margin: -5px;
        }
        
        .clickable-article {
            color: #667eea;
            text-decoration: underline;
            cursor: pointer;
        }
        
        .clickable-article:hover {
            color: #4c51bf;
            font-weight: bold;
        }
        
        .confidence-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8em;
            color: white;
        }
        
        .confidence-high { background: #48bb78; }
        .confidence-medium { background: #ed8936; }
        .confidence-low { background: #f56565; }
        
        /* 팝업 모달 스타일 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.5);
        }
        
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 0;
            border: none;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
            position: relative;
        }
        
        .modal-header h2 {
            margin: 0;
            font-size: 1.5em;
        }
        
        .close {
            color: white;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            position: absolute;
            right: 20px;
            top: 15px;
        }
        
        .close:hover {
            opacity: 0.7;
        }
        
        .modal-body {
            padding: 30px;
        }
        
        .article-section {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .article-section h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .article-content {
            line-height: 1.6;
            color: #4a5568;
            font-size: 1em;
        }
        
        .related-articles {
            margin-top: 20px;
        }
        
        .related-article-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .related-article-item:hover {
            background: #f0f8ff;
            transform: translateX(5px);
        }
        
        .related-article-title {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        .related-article-preview {
            color: #718096;
            font-size: 0.9em;
        }
        
        .input-section {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .input-field {
            flex: 1;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-field:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .send-button:hover {
            background: #5a67d8;
        }
        
        .send-button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
        }
        
        .examples {
            background: rgba(255, 255, 255, 0.9);
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .examples h3 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .example-questions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .example-question {
            background: white;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .example-question:hover {
            background: #f0f8ff;
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .modal-content {
                width: 95%;
                margin: 10% auto;
            }
            
            .example-questions {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ 도시정비사업 법령 전문 AI 챗봇</h1>
            <p>📋 조문 클릭으로 상세 정보를 확인할 수 있습니다!</p>
        </div>
        
        <div class="stats-panel" id="statsPanel">
            <div id="statsContent">통계 로딩 중...</div>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message bot-message">
                    <strong>🤖 AI 챗봇:</strong><br>
                    안녕하세요! 도시정비사업 법령 전문 AI 챗봇입니다.<br>
                    💡 <strong>새로운 기능:</strong> 검색 결과의 조문을 클릭하면 상세 정보를 볼 수 있습니다!
                </div>
            </div>
            
            <div class="input-section">
                <input type="text" id="queryInput" class="input-field" 
                       placeholder="질문을 입력하세요... (예: 도시정비사업이란 무엇인가요?)"
                       onkeypress="handleKeyPress(event)">
                <button id="sendButton" class="send-button" onclick="sendQuery()">전송</button>
            </div>
        </div>
        
        <div class="examples">
            <h3>💡 예시 질문들</h3>
            <div class="example-questions">
                <div class="example-question" onclick="setQuery('도시정비사업이란 무엇인가요?')">
                    도시정비사업이란 무엇인가요?
                </div>
                <div class="example-question" onclick="setQuery('조합설립인가 절차를 알려주세요')">
                    조합설립인가 절차를 알려주세요
                </div>
                <div class="example-question" onclick="setQuery('재건축 안전진단 기준은?')">
                    재건축 안전진단 기준은?
                </div>
                <div class="example-question" onclick="setQuery('주민동의 요건이 궁금해요')">
                    주민동의 요건이 궁금해요
                </div>
                <div class="example-question" onclick="setQuery('정비구역 지정 절차는?')">
                    정비구역 지정 절차는?
                </div>
                <div class="example-question" onclick="setQuery('추진위원회 구성 방법')">
                    추진위원회 구성 방법
                </div>
            </div>
        </div>
    </div>

    <!-- 조문 상세 정보 팝업 모달 -->
    <div id="articleModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">조문 상세 정보</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body" id="modalBody">
                <div id="modalContent">로딩 중...</div>
            </div>
        </div>
    </div>

    <script>
        // 통계 업데이트
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('statsContent').innerHTML = 
                            '<div style="color: red;">❌ 통계 오류</div>';
                        return;
                    }
                    
                    const stats = data.system_stats;
                    const session = data.session_stats;
                    
                    document.getElementById('statsContent').innerHTML = `
                        <div><strong>📊 시스템 통계</strong></div>
                        <div>📚 법령: ${stats.graph_stats.Law || 0}개</div>
                        <div>📄 조문: ${stats.graph_stats.Article || 0}개</div>
                        <div>🧠 임베딩: ${stats.embedding_stats.total_chunks}개</div>
                        <div>🔍 질문: ${session.query_count}회</div>
                        <div>⏱️ 시간: ${session.session_duration}</div>
                    `;
                })
                .catch(error => {
                    console.error('통계 업데이트 오류:', error);
                });
        }
        
        // 페이지 로드 시 통계 로드
        updateStats();
        setInterval(updateStats, 10000); // 10초마다 업데이트
        
        // 질문 전송
        function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            
            if (!query) return;
            
            // 사용자 메시지 추가
            addMessage(query, 'user');
            
            // 입력 필드 초기화 및 비활성화
            input.value = '';
            document.getElementById('sendButton').disabled = true;
            
            // 로딩 메시지 추가
            const loadingId = addMessage('🔍 검색 중...', 'bot');
            
            // API 호출
            fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                // 로딩 메시지 제거
                document.getElementById(loadingId).remove();
                
                if (data.error) {
                    addMessage(`❌ 오류: ${data.error}`, 'bot');
                } else {
                    displaySearchResults(data);
                }
                
                // 버튼 재활성화
                document.getElementById('sendButton').disabled = false;
                
                // 통계 업데이트
                updateStats();
            })
            .catch(error => {
                document.getElementById(loadingId).remove();
                addMessage(`❌ 검색 중 오류가 발생했습니다: ${error.message}`, 'bot');
                document.getElementById('sendButton').disabled = false;
            });
        }
        
        // 메시지 추가
        function addMessage(content, sender) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg_' + Date.now();
            messageDiv.id = messageId;
            messageDiv.className = `message ${sender}-message`;
            
            if (sender === 'user') {
                messageDiv.innerHTML = `<strong>👤 나:</strong><br>${content}`;
            } else {
                messageDiv.innerHTML = `<strong>🤖 AI 챗봇:</strong><br>${content}`;
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageId;
        }
        
        // 검색 결과 표시 (클릭 기능 포함)
        function displaySearchResults(data) {
            let resultHtml = `<strong>🤖 AI 챗봇:</strong><br>`;
            
            if (data.results.length === 0) {
                resultHtml += `❌ "${data.query}"에 대한 관련 법령을 찾을 수 없습니다.<br>`;
                resultHtml += `💡 다른 키워드로 다시 질문해보세요.`;
            } else {
                resultHtml += `🔍 "${data.query}"에 대한 검색 결과 (${data.search_time}):<br><br>`;
                
                data.results.forEach((result, index) => {
                    const confidenceClass = getConfidenceClass(result.confidence);
                    
                    resultHtml += `
                        <div class="search-result">
                            <div class="result-header" onclick="openArticleModal('${result.article_number}', '${result.law_id}', '${result.law_name}')">
                                <span class="clickable-article">📋 ${result.rank}. ${result.article_number}</span>
                                <span class="confidence-badge ${confidenceClass}">
                                    ${result.confidence} (${(result.score * 100).toFixed(0)}%)
                                </span>
                            </div>
                            ${result.law_name !== 'N/A' ? `<div><strong>📚 출처:</strong> ${result.law_name}</div>` : ''}
                            <div><strong>📄 내용:</strong> ${formatContent(result.content)}</div>
                            <div style="margin-top: 10px; font-size: 0.9em; color: #667eea;">
                                💡 조문을 클릭하면 상세 정보를 볼 수 있습니다
                            </div>
                        </div>
                    `;
                });
                
                resultHtml += `<br>💡 총 ${data.result_count}개의 관련 조문을 찾았습니다.`;
            }
            
            addMessage(resultHtml, 'bot');
        }
        
        // 조문 상세 모달 열기 - 새로운 기능!
        function openArticleModal(articleNumber, lawId, lawName) {
            const modal = document.getElementById('articleModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalContent = document.getElementById('modalContent');
            
            // 모달 제목 설정
            modalTitle.textContent = `${articleNumber} - ${lawName}`;
            
            // 로딩 표시
            modalContent.innerHTML = '<div style="text-align: center; padding: 40px;">🔍 조문 상세 정보를 불러오는 중...</div>';
            
            // 모달 표시
            modal.style.display = 'block';
            
            // API 호출
            fetch('/api/article/detail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    article_number: articleNumber, 
                    law_id: lawId 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    modalContent.innerHTML = `<div style="color: red;">❌ ${data.error}</div>`;
                } else {
                    displayArticleDetail(data);
                }
            })
            .catch(error => {
                modalContent.innerHTML = `<div style="color: red;">❌ 오류: ${error.message}</div>`;
            });
        }
        
        // 조문 상세 정보 표시
        function displayArticleDetail(data) {
            const modalContent = document.getElementById('modalContent');
            const article = data.article;
            
            let html = `
                <div class="article-section">
                    <h3>📋 조문 정보</h3>
                    <div class="article-content">
                        <p><strong>조문 번호:</strong> ${article.article_number}</p>
                        <p><strong>소속 법령:</strong> ${article.law_name}</p>
                        ${article.section ? `<p><strong>편장절:</strong> ${article.section}</p>` : ''}
                        ${article.category ? `<p><strong>법령 분류:</strong> ${article.category}</p>` : ''}
                    </div>
                </div>
                
                <div class="article-section">
                    <h3>📄 조문 내용</h3>
                    <div class="article-content">
                        ${formatContent(article.content)}
                    </div>
                </div>
            `;
            
            // 관련 조문 표시
            if (data.related_articles && data.related_articles.length > 0) {
                html += `
                    <div class="article-section">
                        <h3>🔗 관련 조문 (${data.total_related}개)</h3>
                        <div class="related-articles">
                `;
                
                data.related_articles.forEach(related => {
                    html += `
                        <div class="related-article-item" onclick="openArticleModal('${related.article_number}', '${article.law_id}', '${article.law_name}')">
                            <div class="related-article-title">${related.article_number}</div>
                            <div class="related-article-preview">${related.content.substring(0, 100)}...</div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            // 교차 참조 표시
            if (data.cross_references && data.cross_references.length > 0) {
                html += `
                    <div class="article-section">
                        <h3>📎 교차 참조</h3>
                        <div class="related-articles">
                `;
                
                data.cross_references.forEach(ref => {
                    html += `
                        <div class="related-article-item" onclick="openArticleModal('${ref.article_number}', '${article.law_id}', '${article.law_name}')">
                            <div class="related-article-title">${ref.article_number}</div>
                            <div class="related-article-preview">${ref.content.substring(0, 100)}...</div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            modalContent.innerHTML = html;
        }
        
        // 모달 닫기
        function closeModal() {
            document.getElementById('articleModal').style.display = 'none';
        }
        
        // 모달 외부 클릭 시 닫기
        window.onclick = function(event) {
            const modal = document.getElementById('articleModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
        
        // 신뢰도에 따른 CSS 클래스 반환
        function getConfidenceClass(confidence) {
            switch(confidence) {
                case '매우 높음':
                case '높음':
                    return 'confidence-high';
                case '보통':
                    return 'confidence-medium';
                default:
                    return 'confidence-low';
            }
        }
        
        // 내용 포맷팅
        function formatContent(content) {
            return content.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
        }
        
        // 키보드 이벤트 처리
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendQuery();
            }
        }
        
        // 예시 질문 설정
        function setQuery(query) {
            document.getElementById('queryInput').value = query;
            sendQuery();
        }
    </script>
</body>
</html>"""
    
    # 파일 저장
    with open(os.path.join(templates_dir, "index_enhanced.html"), "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    # 템플릿 파일 생성
    create_templates()
    
    # 시스템 초기화
    if not initialize_system():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    print("\n🌐 업그레이드된 웹 서버를 시작합니다...")
    print("   📱 브라우저에서 http://localhost:9090 으로 접속하세요")
    print("   🎯 새로운 기능: 조문 클릭 시 상세 정보 팝업")
    print("   🛑 서버 종료: Ctrl+C")
    
    # Flask 앱 실행
    app.run(host='0.0.0.0', port=9090, debug=False) 