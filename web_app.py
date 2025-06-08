#!/usr/bin/env python3
"""
도시정비사업 법령 전문 AI 챗봇 웹 애플리케이션
Flask 기반 웹서버로 업그레이드된 RAG 시스템 제공
"""

import os
import sys
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# 환경 변수에서 설정 로드
os.environ.setdefault('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', 'python')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 프로덕션/개발 환경 감지
PRODUCTION = os.environ.get('FLASK_ENV', 'development') == 'production'

try:
    from src.graph.legal_graph import LegalGraphManager
    from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("   프로젝트 디렉토리에서 실행하고 있는지 확인하세요.")
    sys.exit(1)

# 전역 변수
graph_manager = None
rag_pipeline = None
session_stats = {
    'start_time': datetime.now(),
    'query_count': 0
}

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS 설정 - 프로덕션에서는 제한적으로
if PRODUCTION:
    allowed_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    CORS(app, origins=allowed_origins if allowed_origins != ['*'] else None)
else:
    CORS(app)

def initialize_system():
    """시스템 초기화"""
    global graph_manager, rag_pipeline
    
    try:
        print("🤖 도시정비사업 법령 전문 AI 챗봇 웹 서버 초기화 중...")
        
        # Neo4j 연결 설정
        neo4j_uri = os.environ.get('NEO4J_URI')
        neo4j_username = os.environ.get('NEO4J_USERNAME')
        neo4j_password = os.environ.get('NEO4J_PASSWORD')
        
        if not all([neo4j_uri, neo4j_username, neo4j_password]):
            if PRODUCTION:
                print("❌ 프로덕션 환경에서 NEO4J 환경변수가 설정되지 않았습니다.")
                return False
            else:
                print("   🔗 개발 환경: 기본 Neo4j 설정 사용")
                # 개발 환경에서는 환경변수가 없어도 기본값으로 시도
                os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
                os.environ.setdefault('NEO4J_USERNAME', 'neo4j')
                os.environ.setdefault('NEO4J_PASSWORD', 'password')
                os.environ.setdefault('NEO4J_DATABASE', 'neo4j')
        
        print("   🔗 Neo4j 데이터베이스 연결 중...")
        # LegalGraphManager는 환경변수를 직접 사용하므로 매개변수 없이 호출
        graph_manager = LegalGraphManager()
        
        print("   🧠 RAG 검색 시스템 초기화 중...")
        rag_pipeline = EnhancedRAGPipeline(graph_manager)
        
        print("✅ 시스템 초기화 완료!")
        try:
            # 법령 데이터 통계 (기본 쿼리로 대체)
            with graph_manager.driver.session() as session:
                law_count = session.run("MATCH (l:Law) RETURN count(l) as count").single()['count']
                article_count = session.run("MATCH (a:Article) RETURN count(a) as count").single()['count']
            print(f"   📄 법령 데이터: {law_count}개 법령, {article_count}개 조문")
        except Exception as e:
            print(f"   📄 법령 데이터: 통계 확인 중 오류 ({e})")
        
        try:
            embedding_count = rag_pipeline.get_embedding_count()
            print(f"   🧠 임베딩: {embedding_count}개 청크")
        except Exception as e:
            print(f"   🧠 임베딩: 통계 확인 중 오류 ({e})")
        
        return True
        
    except Exception as e:
        print(f"❌ 시스템 초기화 오류: {e}")
        if not PRODUCTION:
            import traceback
            traceback.print_exc()
        return False

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(get_html_template())

@app.route('/api/search', methods=['POST'])
def search():
    """검색 API 엔드포인트"""
    global session_stats
    
    try:
        start_time = time.time()
        
        # 디버그 로깅
        if not PRODUCTION:
            print("🔍 [DEBUG] /api/search 엔드포인트 호출됨")
        
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({'error': 'JSON 형식의 요청이 필요합니다'}), 400
        
        data = request.get_json()
        if not PRODUCTION:
            print(f"📊 [DEBUG] 받은 데이터: {data}")
        
        if not data or 'query' not in data:
            return jsonify({'error': '검색어(query)가 필요합니다'}), 400
        
        query = data['query'].strip()
        if not PRODUCTION:
            print(f"🔎 [DEBUG] 추출된 쿼리: '{query}'")
        
        if not query:
            return jsonify({'error': '검색어를 입력해주세요'}), 400
        
        # 세션 통계 업데이트
        session_stats['query_count'] += 1
        if not PRODUCTION:
            print(f"📈 [DEBUG] 세션 정보 업데이트: 쿼리 카운트 = {session_stats['query_count']}")
        
        # RAG 시스템 초기화 확인
        if not rag_pipeline:
            return jsonify({'error': 'RAG 시스템이 초기화되지 않았습니다'}), 500
        
        # 검색 실행
        if not PRODUCTION:
            print("🚀 [DEBUG] RAG 검색 시작...")
        
        search_results = rag_pipeline.search(query)
        search_time = time.time() - start_time
        
        if not PRODUCTION:
            print(f"⏱️ [DEBUG] 검색 완료: {search_time:.3f}초, 결과 개수: {len(search_results) if search_results else 0}")
        
        # 결과 포맷팅
        formatted_results = []
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                try:
                    # 메타데이터 추출
                    metadata = result.get('metadata', {})
                    
                    # 메타데이터에서 정보 추출 및 정규화
                    article_number = metadata.get('article_number', 'N/A')
                    law_name = metadata.get('law_name', 'N/A')
                    law_id = metadata.get('law_id', 'N/A')
                    section = metadata.get('section', metadata.get('section', 'N/A'))
                    
                    # 점수 및 신뢰도 계산
                    score = result.get('combined_score', result.get('vector_score', result.get('keyword_score', 0)))
                    confidence = get_confidence_level(score)
                    
                    formatted_result = {
                        'rank': i,
                        'article_number': article_number,
                        'content': result.get('content', ''),
                        'full_content': result.get('content', ''),
                        'law_name': law_name,
                        'law_id': law_id,
                        'section': section,
                        'score': score,
                        'confidence': confidence
                    }
                    
                    formatted_results.append(formatted_result)
                    
                except Exception as e:
                    if not PRODUCTION:
                        print(f"❌ [DEBUG] 결과 포맷팅 오류 {i}: {e}")
                    continue
        
        # 응답 데이터 구성
        response_data = {
            'query': query,
            'results': formatted_results,
            'search_time': f"{search_time:.3f}초",
            'result_count': len(formatted_results)
        }
        
        if not PRODUCTION:
            print(f"📤 [DEBUG] 응답 데이터: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"검색 중 오류가 발생했습니다: {str(e)}"
        if not PRODUCTION:
            print(f"❌ [DEBUG] API 오류: {error_msg}")
            import traceback
            traceback.print_exc()
        
        return jsonify({'error': error_msg}), 500

@app.route('/api/stats')
def get_stats():
    """시스템 통계 API"""
    try:
        # 현재 시간 계산
        current_time = datetime.now()
        duration = current_time - session_stats['start_time']
        
        # 시스템 통계 수집
        system_stats = {
            'graph_stats': {},
            'embedding_stats': {'total_chunks': 0}
        }
        
        if graph_manager:
            try:
                laws = graph_manager.get_all_laws()
                articles = graph_manager.get_all_articles()
                system_stats['graph_stats'] = {
                    'Law': len(laws),
                    'Article': len(articles)
                }
            except Exception as e:
                if not PRODUCTION:
                    print(f"그래프 통계 수집 오류: {e}")
        
        if rag_pipeline:
            try:
                system_stats['embedding_stats']['total_chunks'] = rag_pipeline.get_embedding_count()
            except Exception as e:
                if not PRODUCTION:
                    print(f"임베딩 통계 수집 오류: {e}")
        
        # 세션 통계
        session_data = {
            'session_duration': str(duration).split('.')[0],  # 마이크로초 제거
            'query_count': session_stats['query_count'],
            'start_time': session_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'system_stats': system_stats,
            'session_stats': session_data
        })
        
    except Exception as e:
        error_msg = f"통계 수집 중 오류: {str(e)}"
        if not PRODUCTION:
            print(f"❌ 통계 API 오류: {error_msg}")
        return jsonify({'error': error_msg}), 500

def get_confidence_level(score):
    """점수 기반 신뢰도 계산"""
    if score >= 0.8:
        return "매우 높음"
    elif score >= 0.6:
        return "높음"
    elif score >= 0.4:
        return "보통"
    else:
        return "낮음"

def get_html_template():
    """HTML 템플릿 반환"""
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏗️ 도시정비사업 법령 AI 챗봇</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 30px;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 500px;
        }
        
        .chat-messages {
            flex: 1;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
            margin-bottom: 20px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 12px;
            line-height: 1.6;
        }
        
        .user-message {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        
        .bot-message {
            background: #f1f8e9;
            border-left: 4px solid #4caf50;
        }
        
        .search-result {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .confidence-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        .input-container input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 1em;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-container input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 15px 30px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .sidebar {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
        }
        
        .stats {
            margin-bottom: 30px;
        }
        
        .stats h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .examples h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .example-questions {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .example-question {
            padding: 12px;
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .example-question:hover {
            background: #e3f2fd;
            border-color: #2196f3;
            transform: translateY(-1px);
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .container {
                padding: 20px;
                margin: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ 도시정비사업 법령 AI 챗봇</h1>
            <p>도시 및 주거환경정비법, 빈집 정비 특례법 등 관련 법령을 AI로 검색하세요</p>
        </div>
        
        <div class="main-content">
            <div class="chat-container">
                <div id="chatMessages" class="chat-messages">
                    <div class="message bot-message">
                        <strong>🤖 AI 챗봇:</strong><br>
                        안녕하세요! 도시정비사업 법령 전문 AI 챗봇입니다. 🏠<br>
                        도시정비사업, 재건축, 재개발 등에 관한 법령을 검색해보세요!
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" 
                           id="queryInput" 
                           placeholder="예: 조합설립인가 절차를 알려주세요" 
                           onkeypress="handleKeyPress(event)">
                    <button id="sendButton" class="send-button" onclick="sendQuery()">전송</button>
                </div>
            </div>
            
            <div class="sidebar">
                <div class="stats">
                    <h3>📊 시스템 현황</h3>
                    <div id="statsContent">로딩 중...</div>
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
                    document.getElementById('statsContent').innerHTML = 
                        '<div style="color: red;">❌ 통계 로딩 실패</div>';
                });
        }
        
        // 페이지 로드 시 통계 로드
        updateStats();
        setInterval(updateStats, 10000); // 10초마다 업데이트
        
        // 질문 전송
        function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            
            if (!query) {
                alert('질문을 입력해주세요!');
                return;
            }
            
            console.log('전송 버튼 클릭됨, 쿼리:', query);
            
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
            .then(response => {
                console.log('API 응답 상태:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('API 응답 데이터:', data);
                
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
                console.error('API 호출 오류:', error);
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
                messageDiv.innerHTML = content;
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageId;
        }
        
        // 검색 결과 표시
        function displaySearchResults(data) {
            console.log('검색 결과 표시:', data);
            
            let resultHtml = `<strong>🤖 AI 챗봇:</strong><br>`;
            
            if (!data.results || data.results.length === 0) {
                resultHtml += `❌ "${data.query || '입력된 검색어'}"에 대한 관련 법령을 찾을 수 없습니다.<br>`;
                resultHtml += `💡 다른 키워드로 다시 질문해보세요.`;
            } else {
                resultHtml += `🔍 "${data.query || '입력된 검색어'}"에 대한 검색 결과 (${data.search_time || 'N/A'}):<br><br>`;
                
                data.results.forEach((result, index) => {
                    const score = result.score || 0;
                    const confidence = result.confidence || '정보 없음';
                    const rank = result.rank || (index + 1);
                    const article_number = result.article_number || "N/A";
                    const law_name = result.law_name || "N/A";
                    const content = result.content || "내용 없음";

                    const confidenceClass = getConfidenceClass(confidence);
                    
                    resultHtml += `
                        <div class="search-result">
                            <div class="result-header">
                                <span>📋 ${rank}. ${article_number}</span>
                                <span class="confidence-badge ${confidenceClass}">
                                    ${confidence} (${(score * 100).toFixed(0)}%)
                                </span>
                            </div>
                            ${law_name !== 'N/A' ? `<div><strong>📚 출처:</strong> ${law_name}</div>` : ''}
                            <div><strong>📄 내용:</strong> ${formatContent(content)}</div>
                        </div>
                    `;
                });
                
                resultHtml += `<br>💡 총 ${data.result_count || data.results.length}개의 관련 조문을 찾았습니다.`;
            }
            
            addMessage(resultHtml, 'bot');
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
            if (!content) return '내용 없음';
            const formatted = content.replace(/\\\\n/g, '<br>').replace(/\\\\r/g, '<br>');
            if (formatted.length > 300) {
                return formatted.substring(0, 300) + '...';
            }
            return formatted;
        }
        
        // 키보드 이벤트 처리
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendQuery();
            }
        }
        
        // 예시 질문 설정
        function setQuery(query) {
            console.log('예시 질문 클릭:', query);
            document.getElementById('queryInput').value = query;
            sendQuery();
        }
    </script>
</body>
</html>"""

if __name__ == "__main__":
    # 시스템 초기화
    if not initialize_system():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    # 포트 설정 (Railway는 PORT 환경변수 사용)
    port = int(os.environ.get('PORT', 9876))
    debug = not PRODUCTION
    
    if PRODUCTION:
        print(f"🌐 프로덕션 서버 시작 (포트: {port})")
    else:
        print(f"\n🌐 [DEBUG] 개발 서버 시작 (포트: {port})")
        print("   📱 브라우저에서 http://localhost:9876 으로 접속하세요")
        print("   🎯 새로운 기능: 조문 클릭 시 상세 정보 팝업")
        print("   🛑 서버 종료: Ctrl+C")
        print("   🔧 디버그 모드 활성화!")
    
    # Flask 앱 실행
    app.run(host='0.0.0.0', port=port, debug=debug) 