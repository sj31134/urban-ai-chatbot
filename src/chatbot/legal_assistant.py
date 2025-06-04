"""
도시정비 법령 전문 AI 챗봇
Streamlit 기반 사용자 인터페이스
"""

# 필요한 라이브러리 import
import os  # 운영체제 관련 기능
import sys  # 시스템 관련 기능
import streamlit as st  # 웹 애플리케이션 프레임워크

# Streamlit 페이지 설정 (반드시 다른 streamlit 명령보다 먼저)
if 'page_config_set' not in st.session_state:
    st.set_page_config(
        page_title="도시정비 법령 전문 AI",
        page_icon="🏗️", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.session_state.page_config_set = True

import logging  # 로그 기록
from datetime import datetime  # 날짜/시간 처리
from typing import Dict, List, Any  # 타입 힌트
import json  # JSON 데이터 처리

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # 상위 3단계 디렉토리 경로
sys.path.insert(0, project_root)  # 시스템 경로에 추가

# 프로젝트 내부 모듈 import
from src.graph.legal_graph import LegalGraphManager  # Neo4j 그래프 관리자
from src.rag.legal_rag_chain import LegalRAGChain  # RAG 체인 클래스
from dotenv import load_dotenv  # 환경변수 로드

# 환경 변수 로드
load_dotenv()  # .env 파일에서 환경변수 읽기

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # INFO 레벨 로깅 설정
logger = logging.getLogger(__name__)  # 현재 모듈용 로거 생성


class LegalAssistant:
    """도시정비 법령 전문 AI 어시스턴트"""
    
    def __init__(self):
        """어시스턴트 초기화"""
        self.initialize_session_state()  # 세션 상태 초기화
        
        # load_components의 결과를 세션 상태에 반영
        if not st.session_state.get('system_components_loaded', False): # 한 번만 로드하도록 플래그 사용
            self._load_and_store_components()
            st.session_state.system_components_loaded = True
    
    def initialize_session_state(self):
        """Streamlit 세션 상태 초기화"""
        if 'chat_history' not in st.session_state:  # 채팅 기록이 없으면
            st.session_state.chat_history = []  # 빈 리스트로 초기화
        
        if 'graph_manager' not in st.session_state:  # 그래프 매니저가 없으면
            st.session_state.graph_manager = None  # None으로 초기화
        
        if 'rag_chain' not in st.session_state:  # RAG 체인이 없으면
            st.session_state.rag_chain = None  # None으로 초기화

        if 'backup_llm' not in st.session_state: # backup_llm도 세션 상태로 관리
            st.session_state.backup_llm = None

        if 'system_ready' not in st.session_state:  # 시스템 준비 상태가 없으면
            st.session_state.system_ready = False  # False로 초기화
        
        if 'system_components_loaded' not in st.session_state: # 로드 여부 플래그
            st.session_state.system_components_loaded = False

    def _load_and_store_components(self):
        """시스템 구성 요소 로드 및 세션 상태 저장"""
        try:
            logger.info("LegalGraphManager 초기화 시작...")
            graph_manager = LegalGraphManager()
            logger.info("LegalGraphManager 초기화 완료.")
            
            logger.info("LegalRAGChain 초기화 시작...")
            rag_chain = LegalRAGChain(graph_manager)
            logger.info("LegalRAGChain 초기화 완료.")
            
            st.session_state.graph_manager = graph_manager
            st.session_state.rag_chain = rag_chain
            st.session_state.system_ready = True
            logger.info("그래프 RAG 시스템 초기화 성공.")
            
        except Exception as e:
            logger.error(f"그래프 RAG 시스템 초기화 중 예외 발생 타입: {type(e)}")
            logger.error(f"그래프 RAG 시스템 초기화 실패 메시지: {str(e)}")
            import traceback
            logger.error(f"그래프 RAG 시스템 Traceback: {traceback.format_exc()}")
            
            st.session_state.graph_manager = None # 명시적 None 할당
            st.session_state.rag_chain = None     # 명시적 None 할당
            logger.info("기본 Gemini AI 모드로 전환합니다.")
            
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                # load_dotenv() # 이미 상단에서 호출되었거나, LegalGraphManager 등에서 호출될 수 있음

                backup_llm_model = os.getenv("FALLBACK_GEMINI_MODEL", "gemini-1.5-flash")
                google_api_key = os.getenv("GOOGLE_API_KEY")

                if not google_api_key:
                    logger.error("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다. 백업 LLM을 초기화할 수 없습니다.")
                    raise ValueError("GOOGLE_API_KEY가 없습니다.")

                logger.info(f"백업 LLM ({backup_llm_model}) 초기화 시작...")
                backup_llm = ChatGoogleGenerativeAI(
                    model=backup_llm_model,
                    google_api_key=google_api_key,
                    temperature=0.1
                )
                st.session_state.backup_llm = backup_llm
                st.session_state.system_ready = True # 백업 모드도 준비된 상태
                logger.info(f"백업 LLM ({backup_llm_model}) 초기화 성공.")
                
            except Exception as e2:
                logger.error(f"백업 Gemini LLM 초기화 실패: {e2}")
                logger.error(f"백업 LLM Traceback: {traceback.format_exc()}")
                st.session_state.backup_llm = None
                st.session_state.system_ready = False # 백업 LLM도 실패하면 시스템 미준비
    
    def setup_page_config(self):
        """페이지 설정"""
        st.set_page_config(  # Streamlit 페이지 설정
            page_title="도시정비 법령 전문 AI",  # 페이지 제목
            page_icon="🏗️",  # 페이지 아이콘
            layout="wide",  # 넓은 레이아웃 사용
            initial_sidebar_state="expanded"  # 사이드바 확장 상태로 시작
        )
        
        # CSS 스타일링
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .chat-message {
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 5px solid #3B82F6;
        }
        
        .user-message {
            background-color: #EFF6FF;
            border-left-color: #3B82F6;
        }
        
        .assistant-message {
            background-color: #F0FDF4;
            border-left-color: #10B981;
        }
        
        .source-box {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        }
        
        .confidence-high {
            color: #10B981;
            font-weight: bold;
        }
        
        .confidence-medium {
            color: #F59E0B;
            font-weight: bold;
        }
        
        .confidence-low {
            color: #EF4444;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)  # HTML을 직접 렌더링 허용
    
    def render_header(self):
        """헤더 렌더링"""
        st.markdown("""
        <div class="main-header">
            <h1>🏗️ 도시정비사업 법령 전문 AI 챗봇</h1>
            <p>도시 및 주거환경정비법, 소규모주택정비법 등 관련 법령 정보를 정확하게 제공합니다</p>
        </div>
        """, unsafe_allow_html=True)  # HTML 헤더 렌더링
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:  # 사이드바 컨텍스트 내에서
            st.header("💡 시스템 정보")  # 시스템 정보 헤더
            
            # 시스템 상태
            if st.session_state.system_ready:  # 시스템이 준비되었으면
                st.success("✅ 시스템 준비 완료")  # 성공 메시지 표시
            else:  # 시스템이 준비되지 않았으면
                st.error("❌ 시스템 초기화 필요")  # 에러 메시지 표시
            
            st.markdown("---")  # 구분선 추가
            
            # 주요 기능 안내
            st.header("🔍 주요 기능")  # 주요 기능 헤더
            st.markdown("""
            - **법령 검색**: 키워드로 관련 조문 찾기
            - **그래프 탐색**: 조문 간 연관관계 분석
            - **출처 제공**: 정확한 법령 조문 명시
            - **신뢰도 평가**: 답변의 정확성 평가
            """)  # 기능 설명 마크다운
            
            st.markdown("---")  # 구분선 추가
            
            # 질의 예시
            st.header("💬 질의 예시")  # 질의 예시 헤더
            example_queries = [  # 예시 질문 리스트
                "재개발 조합 설립 요건은?",
                "소규모재개발사업 현금청산 제외 조건",
                "정비사업 시행인가 절차",
                "가로주택정비사업 대상 요건",
                "빈집정비사업 특례 내용"
            ]
            
            for query in example_queries:  # 각 예시 질문에 대해
                if st.button(f"📝 {query}", key=f"example_{hash(query)}"):  # 버튼 클릭 시
                    self.process_query(query)  # 해당 질문 처리
            
            st.markdown("---")  # 구분선 추가
            
            # 채팅 기록 관리
            st.header("🗂️ 채팅 관리")  # 채팅 관리 헤더
            col1, col2 = st.columns(2)  # 2개 컬럼으로 분할
            
            with col1:  # 첫 번째 컬럼
                if st.button("🗑️ 기록 삭제", key="clear_history"):  # 기록 삭제 버튼
                    st.session_state.chat_history = []  # 채팅 기록 초기화
                    st.rerun()  # 페이지 새로고침
            
            with col2:  # 두 번째 컬럼
                if st.button("📥 내보내기", key="export_history"):  # 내보내기 버튼
                    self.export_chat_history()  # 채팅 기록 내보내기 함수 호출
    
    def render_chat_interface(self):
        """채팅 인터페이스 렌더링"""
        # 메시지 출력 영역
        chat_container = st.container()  # 채팅 컨테이너 생성
        
        with chat_container:  # 컨테이너 내에서
            for message in st.session_state.chat_history:  # 각 채팅 메시지에 대해
                self.render_message(message)  # 메시지 렌더링
        
        # 입력 영역
        with st.container():  # 입력 컨테이너
            col1, col2 = st.columns([8, 1])  # 8:1 비율로 컬럼 분할
            
            with col1:  # 첫 번째 컬럼 (입력창)
                user_input = st.text_input(  # 텍스트 입력창
                    "법령에 대해 궁금한 것을 질문해주세요:",  # 플레이스홀더 텍스트
                    key="user_input",  # 고유 키
                    placeholder="예: 재개발 조합 설립 요건은 무엇인가요?"  # 힌트 텍스트
                )
            
            with col2:  # 두 번째 컬럼 (전송 버튼)
                send_button = st.button("📤 전송", key="send_button")  # 전송 버튼
        
        # 메시지 처리
        if send_button and user_input.strip():  # 전송 버튼 클릭하고 입력이 있으면
            self.process_query(user_input.strip())  # 입력 처리
            st.rerun()  # 페이지 새로고침
        
        # Enter 키 처리를 위한 JavaScript
        st.markdown("""
        <script>
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type=text]');
        inputs.forEach(input => {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const button = doc.querySelector('button[kind=primary]');
                    if (button) button.click();
                }
            });
        });
        </script>
        """, unsafe_allow_html=True)  # JavaScript 코드 삽입
    
    def render_message(self, message: Dict[str, Any]):
        """개별 메시지 렌더링"""
        if message["role"] == "user":  # 사용자 메시지인 경우
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 사용자:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)  # 사용자 메시지 HTML 렌더링
            
        elif message["role"] == "assistant":  # AI 어시스턴트 메시지인 경우
            # 신뢰도에 따른 CSS 클래스 결정
            confidence = message.get("confidence", 0.0)  # 신뢰도 값 가져오기
            if confidence >= 0.8:  # 높은 신뢰도
                confidence_class = "confidence-high"
            elif confidence >= 0.6:  # 중간 신뢰도
                confidence_class = "confidence-medium"
            else:  # 낮은 신뢰도
                confidence_class = "confidence-low"
            
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 AI 어시스턴트:</strong>
                <span class="{confidence_class}">신뢰도: {confidence:.2f}</span><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)  # AI 메시지 HTML 렌더링
            
            # 출처 정보 표시
            if message.get("sources"):  # 출처 정보가 있으면
                st.markdown("**📚 관련 법령 조문:**")  # 출처 섹션 헤더
                for i, source in enumerate(message["sources"], 1):  # 각 출처에 대해
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>{i}. {source.get('law_name', '법령명 미상')}</strong><br>
                        <small>조문: {source.get('article_number', 'N/A')} | 
                        유사도: {source.get('similarity_score', 0.0):.3f}</small><br>
                        {source.get('content_preview', '내용 없음')}
                    </div>
                    """, unsafe_allow_html=True)  # 출처 정보 HTML 렌더링
            
            # 관련 조문 추천
            if message.get("related_articles"):  # 관련 조문이 있으면
                st.markdown("**🔗 관련 조문:**")  # 관련 조문 섹션 헤더
                for article in message["related_articles"]:  # 각 관련 조문에 대해
                    st.markdown(f"- {article}")  # 조문 정보 표시
    
    def process_query(self, query: str):
        """사용자 질의 처리"""
        if not query.strip():  # 빈 질의인 경우
            return  # 처리하지 않음
        
        # 질의를 채팅 기록에 추가
        st.session_state.chat_history.append({  # 채팅 기록에 새 항목 추가
            "role": "user",  # 사용자 역할
            "content": query,  # 질의 내용
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시간
        })
        
        # 답변 생성 및 처리
        with st.spinner("답변을 생성하고 있습니다... 🤔"):  # 로딩 스피너 표시
            try:
                # Graph RAG 시스템이 준비된 경우
                if st.session_state.rag_chain and hasattr(st.session_state.rag_chain, 'query_with_sources'):
                    # 정식 RAG 체인 사용
                    result = st.session_state.rag_chain.query_with_sources(query)  # RAG 체인으로 질의 처리
                    
                    # 답변을 채팅 기록에 추가
                    st.session_state.chat_history.append({  # 채팅 기록에 답변 추가
                        "role": "assistant",  # 어시스턴트 역할
                        "content": result["answer"],  # 답변 내용
                        "sources": result.get("sources", []),  # 출처 정보
                        "confidence": result.get("confidence", 0.5),  # 신뢰도
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시간
                    })
                    
                    logger.info(f"그래프 RAG 모드 질의 처리 완료: {query[:50]}...")  # 정보 로그 기록
                
                # 백업 모드 (기본 Gemini AI만 사용)
                elif st.session_state.backup_llm:
                    # 도시정비법 관련 전문 프롬프트
                    backup_prompt = f"""당신은 도시정비사업 법령 전문가입니다. 다음 질문에 대해 정확하고 구체적인 답변을 제공해주세요.

주요 관련 법령:
1. 도시 및 주거환경정비법
2. 소규모주택정비관리지원법 
3. 빈집 및 소규모주택 정비에 관한 특례법
4. 건축법, 도시계획법 관련 조항

질문: {query}

답변 시 유의사항:
- 관련 법령의 조문을 명시하여 근거를 제시해주세요
- 실무적으로 적용 가능한 구체적인 정보를 포함해주세요
- 불확실한 내용은 명확히 구분하여 안내해주세요
- 재개발, 재건축, 소규모정비사업 등의 차이점을 명확히 해주세요

답변:"""
                    
                    try:
                        # Gemini로 답변 생성 (문자열로만 전달)
                        response = st.session_state.backup_llm.invoke(backup_prompt)
                        
                        # 답변 텍스트 추출
                        if hasattr(response, 'content'):
                            answer_text = response.content
                        else:
                            answer_text = str(response)
                        
                        # 백업 모드 답변을 채팅 기록에 추가
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer_text,
                            "sources": [{"source": "기본 AI 모드", "content": "Neo4j Graph RAG가 연결되지 않아 기본 AI 모드로 답변합니다."}],
                            "confidence": 0.7,  # 백업 모드는 중간 신뢰도
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mode": "backup"  # 백업 모드 표시
                        })
                        
                        logger.info(f"백업/테스트 모드 질의 처리 완료: {query[:50]}...")
                        
                    except Exception as gemini_error:
                        # Gemini API 실패 시 더미 응답 제공
                        logger.error(f"Gemini API 오류: {gemini_error}")
                        
                        # 도시정비사업 관련 더미 응답 생성
                        dummy_responses = {
                            "재개발": "재개발 조합 설립을 위해서는 도시 및 주거환경정비법 제16조에 따라 토지면적의 3분의 2 이상, 토지소유자 수의 3분의 2 이상의 동의가 필요합니다.",
                            "소규모": "소규모주택정비법에 따른 소규모재개발사업에서는 현금청산 대상자 중 일정 요건을 충족하는 경우 현금청산에서 제외될 수 있습니다.",
                            "정비사업": "정비사업 시행인가는 도시 및 주거환경정비법 제66조에 따라 사업시행자가 시장·군수에게 신청하며, 관련 서류 검토 후 인가 여부가 결정됩니다.",
                            "가로주택": "가로주택정비사업은 노후·불량건축물이 밀집한 지역에서 소규모로 주거환경을 개선하는 사업입니다.",
                            "빈집": "빈집정비특례법에 따라 장기간 방치된 빈집에 대해서는 특례적인 정비 절차가 적용될 수 있습니다."
                        }
                        
                        # 질의와 관련된 키워드 찾기
                        response_content = "죄송합니다. 현재 AI 서비스에 일시적인 문제가 있습니다."
                        for keyword, response in dummy_responses.items():
                            if keyword in query:
                                response_content = f"[테스트 모드] {response}\n\n※ 현재 테스트 모드로 운영 중입니다. 정확한 법령 정보는 관련 법령을 직접 확인해주세요."
                                break
                        
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": response_content,
                            "sources": [{"source": "테스트 모드", "content": "AI 서비스 문제로 테스트 모드로 답변합니다."}],
                            "confidence": 0.5,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mode": "demo"
                        })
                
                else:
                    # 완전 실패 케이스
                    error_message = """
                    죄송합니다. 현재 시스템에 일시적인 문제가 발생했습니다.
                    
                    **문제 상황:**
                    - Neo4j 그래프 데이터베이스 연결 실패
                    - Gemini AI API 연결 실패
                    
                    **해결 방법:**
                    1. API 키가 올바른지 확인해주세요
                    2. 네트워크 연결을 확인해주세요  
                    3. 잠시 후 다시 시도해주세요
                    
                    관련 문의는 시스템 관리자에게 연락해주세요.
                    """
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": error_message,
                        "sources": [],
                        "confidence": 0.0,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "error": True
                    })
                    
                    logger.error("모든 AI 시스템 연결 실패")
                
            except Exception as e:  # 질의 처리 중 오류 발생 시
                logger.error(f"질의 처리 오류: {e}")  # 에러 로그 기록
                
                # 오류 메시지를 채팅 기록에 추가
                st.session_state.chat_history.append({  # 오류 메시지 추가
                    "role": "assistant",  # 어시스턴트 역할
                    "content": f"죄송합니다. 질의 처리 중 오류가 발생했습니다: {str(e)}",  # 오류 내용
                    "sources": [],  # 빈 출처 목록
                    "confidence": 0.0,  # 신뢰도 0
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 현재 시간
                    "error": True  # 오류 플래그
                })
    
    def export_chat_history(self):
        """채팅 기록 내보내기"""
        if not st.session_state.chat_history:  # 채팅 기록이 없으면
            st.warning("내보낼 채팅 기록이 없습니다.")  # 경고 메시지 표시
            return  # 함수 종료
        
        # JSON 형태로 변환
        export_data = {  # 내보낼 데이터 구조
            "session_info": {  # 세션 정보
                "export_time": datetime.now().isoformat(),  # 내보내기 시간
                "total_messages": len(st.session_state.chat_history)  # 총 메시지 수
            },
            "chat_history": st.session_state.chat_history  # 채팅 기록
        }
        
        # 다운로드 링크 생성
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)  # JSON 문자열로 변환
        st.download_button(  # 다운로드 버튼 생성
            label="📥 JSON 다운로드",  # 버튼 라벨
            data=json_str,  # 다운로드할 데이터
            file_name=f"legal_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",  # 파일명
            mime="application/json"  # MIME 타입
        )
    
    def run(self):
        """어시스턴트 실행"""
        # 시스템 구성 요소 로드
        if not st.session_state.system_ready:  # 시스템이 준비되지 않았으면
            with st.spinner("시스템 초기화 중..."):  # 로딩 스피너와 함께
                self._load_and_store_components()  # 구성 요소 로드
                st.session_state.system_ready = True  # 시스템 준비 상태로 변경
                st.success("시스템 초기화 완료!")  # 성공 메시지 표시
                st.rerun()  # 페이지 새로고침
        
        # 헤더 렌더링
        self.render_header()  # 페이지 헤더 렌더링
        
        # 레이아웃 구성
        col1, col2 = st.columns([3, 1])  # 3:1 비율로 컬럼 분할
        
        with col1:  # 첫 번째 컬럼 (메인 콘텐츠)
            # 메인 채팅 인터페이스
            self.render_chat_interface()  # 채팅 인터페이스 렌더링
        
        with col2:  # 두 번째 컬럼 (사이드바)
            # 사이드바
            self.render_sidebar()  # 사이드바 렌더링


def main():
    """메인 함수"""
    try:
        assistant = LegalAssistant()  # 법령 어시스턴트 객체 생성
        assistant.run()  # 어시스턴트 실행
        
    except Exception as e:  # 예외 발생 시
        st.error(f"어플리케이션 실행 중 오류가 발생했습니다: {str(e)}")  # 에러 메시지 표시
        logger.error(f"어플리케이션 오류: {e}")  # 에러 로그 기록


if __name__ == "__main__":  # 스크립트가 직접 실행될 때
    main()  # 메인 함수 호출 