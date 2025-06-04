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
        print("🔍 [DEBUG] /api/search 엔드포인트 호출됨")
        
        if not is_initialized:
            print("❌ [DEBUG] 시스템이 초기화되지 않았음")
            return jsonify({'error': '시스템이 초기화되지 않았습니다.'}), 500
        
        data = request.get_json()
        print(f"📊 [DEBUG] 받은 데이터: {data}")
        
        query = data.get('query', '').strip()
        print(f"🔎 [DEBUG] 추출된 쿼리: '{query}'")
        
        if not query:
            print("❌ [DEBUG] 빈 쿼리")
            return jsonify({'error': '검색어를 입력해주세요.'}), 400
        
        # 세션 정보 업데이트
        if 'start_time' not in session:
            session['start_time'] = datetime.now().isoformat()
        session['query_count'] = session.get('query_count', 0) + 1
        print(f"📈 [DEBUG] 세션 정보 업데이트: 쿼리 카운트 = {session['query_count']}")
        
        # 검색 수행
        start_time = time.time()
        print("🚀 [DEBUG] RAG 검색 시작...")
        results = rag_pipeline.search(query, search_type="hybrid", k=3)
        search_time = round(time.time() - start_time, 3)
        print(f"⏱️ [DEBUG] 검색 완료: {search_time}초, 결과 개수: {len(results)}")
        
        # 극도로 상세한 디버깅
        print(f"🔍🔍🔍 [DEBUG] 극도로 상세한 디버깅 - 검색 결과:")
        print(f"  RAG 파이프라인 타입: {type(rag_pipeline)}")
        print(f"  결과 타입: {type(results)}")
        print(f"  결과 개수: {len(results)}")
        
        if results:
            for idx, result in enumerate(results):
                print(f"\n  === {idx+1}번째 결과 ===")
                print(f"  - 결과 타입: {type(result)}")
                print(f"  - 결과 키들: {list(result.keys())}")
                print(f"  - 'metadata' 키 존재: {'metadata' in result}")
                print(f"  - 'metadata' 값 타입: {type(result.get('metadata'))}")
                print(f"  - 'metadata' 값: {result.get('metadata')}")
                
                metadata = result.get("metadata", {})
                print(f"  - 추출된 metadata 타입: {type(metadata)}")
                print(f"  - 추출된 metadata: {metadata}")
                
                if isinstance(metadata, dict):
                    print(f"  - metadata 키들: {list(metadata.keys())}")
                    print(f"  - article_number: {metadata.get('article_number')}")
                    print(f"  - law_id: {metadata.get('law_id')}")
                    print(f"  - law_name: {metadata.get('law_name')}")
                    print(f"  - section: {metadata.get('section')}")
                else:
                    print(f"  - ❌ metadata가 딕셔너리가 아님!")
        
        # 결과 포맷팅
        formatted_results = []
        for i, result in enumerate(results, 1):
            # 메타데이터에서 정보 추출
            metadata = result.get("metadata", {})
            print(f"\n  🔧 [DEBUG] {i}번째 결과 포맷팅:")
            print(f"    - 원본 metadata: {metadata}")
            
            article_number = metadata.get("article_number", "N/A")
            law_name = metadata.get("law_name", "N/A") 
            law_id = metadata.get("law_id", "N/A")
            section = metadata.get("section", "")
            
            print(f"    - 추출된 article_number: {article_number}")
            print(f"    - 추출된 law_name: {law_name}")
            print(f"    - 추출된 law_id: {law_id}")
            print(f"    - 추출된 section: {section}")
            
            formatted_result = {
                "rank": i,
                "article_number": article_number,
                "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "full_content": result.get("content", ""),  # 팝업용 전체 내용
                "law_name": law_name,
                "law_id": law_id,  # 팝업용 법령 ID
                "section": section,
                "score": result.get("combined_score", result.get("score", 0)),
                "confidence": get_confidence_level(result.get("combined_score", result.get("score", 0)))
            }
            print(f"    - 최종 formatted_result: {formatted_result}")
            formatted_results.append(formatted_result)
        
        response_data = {
            "query": query,
            "results": formatted_results,
            "search_time": f"{search_time}초",
            "result_count": len(results)
        }
        print(f"📤 [DEBUG] 응답 데이터: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"💥 [DEBUG] 검색 API 오류: {str(e)}")
        import traceback
        print(f"📋 [DEBUG] 오류 트레이스백:")
        traceback.print_exc()
        return jsonify({'error': f'검색 중 오류가 발생했습니다: {str(e)}'}), 500


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


# HTML 템플릿 생성 (기본 기능만)
def create_templates():
    """HTML 템플릿 파일들 생성"""
    
    # templates 디렉토리 생성
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # index_enhanced.html 생성 (기본 기능만)
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>도시정비사업 법령 전문 AI 챗봇</title>
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
            <p>도시정비사업 관련 법령에 대해 무엇이든 물어보세요!</p>
        </div>
        
        <div class="stats-panel" id="statsPanel">
            <div id="statsContent">통계 로딩 중...</div>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message bot-message">
                    <strong>🤖 AI 챗봇:</strong><br>
                    안녕하세요! 도시정비사업 법령 전문 AI 챗봇입니다.<br>
                    도시정비사업, 재개발, 재건축 관련 법령에 대해 질문해주세요.
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
    
    # 파일 저장
    with open(os.path.join(templates_dir, "index_enhanced.html"), "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    # 템플릿 파일 생성 - 수정 완료 후 비활성화
    # create_templates()
    
    # 시스템 초기화
    if not initialize_system():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    print("\n🌐 [DEBUG] 업그레이드된 웹 서버를 디버그 모드로 시작합니다...")
    print("   📱 브라우저에서 http://localhost:9876 으로 접속하세요")
    print("   🎯 새로운 기능: 조문 클릭 시 상세 정보 팝업")
    print("   🛑 서버 종료: Ctrl+C")
    print("   🔧 디버그 모드 활성화!")
    
    # Flask 앱 실행 (디버그 모드로 변경)
    app.run(host='0.0.0.0', port=9876, debug=True) 