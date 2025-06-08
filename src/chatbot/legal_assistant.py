"""
도시정비 법령 전문 AI 챗봇
Streamlit 기반 사용자 인터페이스
"""

import os
import sys
import streamlit as st
import logging
from datetime import datetime
from typing import Dict, List, Any
import json
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.graph.legal_graph import LegalGraphManager
from src.rag.legal_rag_chain import LegalRAGChain

# 환경 변수 로드
load_dotenv()

# Streamlit Community Cloud 호환 환경변수 처리 함수
def get_env_var(key: str, default: str = "") -> str:
    """환경변수 또는 Streamlit secrets에서 값 가져오기"""
    try:
        # 먼저 st.secrets에서 시도 (Streamlit Community Cloud)
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except:
        pass
    
    # 환경변수에서 가져오기 (로컬/Docker)
    return os.getenv(key, default)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalAssistant:
    """도시정비 법령 전문 AI 어시스턴트"""
    
    def __init__(self):
        """어시스턴트 초기화"""
        self.initialize_session_state()
        self.load_components()
    
    def initialize_session_state(self):
        """Streamlit 세션 상태 초기화"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'graph_manager' not in st.session_state:
            st.session_state.graph_manager = None
        
        if 'rag_chain' not in st.session_state:
            st.session_state.rag_chain = None
        
        if 'system_ready' not in st.session_state:
            st.session_state.system_ready = False
    
    @st.cache_resource(ttl=3600, max_entries=1)  # 1시간 TTL, 최대 1개 엔트리
    def load_components(_self):
        """시스템 구성 요소 로드 (캐시 활용)"""
        try:
            # Neo4j 그래프 관리자 초기화
            graph_manager = LegalGraphManager()
            
            # RAG 체인 초기화 (메모리 최적화)
            rag_chain = LegalRAGChain(graph_manager)
            
            return graph_manager, rag_chain, True
            
        except Exception as e:
            logger.error(f"그래프 RAG 시스템 초기화 실패: {e}")
            logger.info("기본 Gemini AI 모드로 전환합니다.")
            
            # 기본 Gemini AI만 사용하는 백업 체인
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from dotenv import load_dotenv
                load_dotenv()
                
                backup_llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=get_env_var("GOOGLE_API_KEY")
                )
                
                return None, backup_llm, True
                
            except Exception as e2:
                logger.error(f"백업 시스템 초기화도 실패: {e2}")
                return None, None, False
    
    def setup_page_config(self):
        """페이지 설정"""
        st.set_page_config(
            page_title="도시정비 법령 전문 AI",
            page_icon="🏗️",
            layout="wide",
            initial_sidebar_state="expanded"
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
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """헤더 렌더링"""
        st.markdown("""
        <div class="main-header">
            <h1>🏗️ 도시정비사업 법령 전문 AI 챗봇</h1>
            <p>도시 및 주거환경정비법, 소규모주택정비법 등 관련 법령 정보를 정확하게 제공합니다</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            st.header("💡 시스템 정보")
            
            # 시스템 상태
            if st.session_state.system_ready:
                st.success("✅ 시스템 준비 완료")
            else:
                st.error("❌ 시스템 초기화 필요")
            
            st.markdown("---")
            
            # 주요 기능 안내
            st.header("🔍 주요 기능")
            st.markdown("""
            - **법령 검색**: 키워드로 관련 조문 찾기
            - **그래프 탐색**: 조문 간 연관관계 분석
            - **출처 제공**: 정확한 법령 조문 명시
            - **신뢰도 평가**: 답변의 정확성 평가
            """)
            
            st.markdown("---")
            
            # 질의 예시
            st.header("💬 질의 예시")
            example_queries = [
                "재개발 조합 설립 요건은?",
                "소규모재개발사업 현금청산 제외 조건",
                "정비사업 시행인가 절차",
                "가로주택정비사업 대상 요건",
                "빈집정비사업 특례 내용"
            ]
            
            for query in example_queries:
                if st.button(f"📝 {query}", key=f"example_{hash(query)}"):
                    self.process_query(query)
            
            st.markdown("---")
            
            # 채팅 기록 관리
            st.header("🗂️ 채팅 관리")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 기록 삭제"):
                    st.session_state.chat_history = []
                    st.rerun()
            
            with col2:
                if st.button("💾 기록 저장"):
                    self.export_chat_history()
            
            # 통계 정보
            if st.session_state.chat_history:
                st.markdown("---")
                st.header("📊 세션 통계")
                st.metric("총 질의 수", len([msg for msg in st.session_state.chat_history if msg["role"] == "user"]))
                
                # 평균 신뢰도 계산
                confidences = [
                    msg.get("confidence", 0) 
                    for msg in st.session_state.chat_history 
                    if msg["role"] == "assistant" and "confidence" in msg
                ]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    st.metric("평균 신뢰도", f"{avg_confidence:.2f}")
    
    def render_chat_interface(self):
        """채팅 인터페이스 렌더링"""
        # 제안된 질의가 있는 경우 처리
        if hasattr(st.session_state, 'suggested_query') and st.session_state.suggested_query:
            suggested_query = st.session_state.suggested_query
            del st.session_state.suggested_query
            self.process_query(suggested_query)
            st.rerun()
        
        # 디버깅 정보 (개발용)
        if st.checkbox("🔧 디버그 모드", key="debug_mode"):
            st.write(f"**채팅 기록 수:** {len(st.session_state.chat_history)}")
            if st.session_state.chat_history:
                st.write("**최근 메시지:**")
                for i, msg in enumerate(st.session_state.chat_history[-3:]):
                    st.json({f"메시지 {i+1}": {
                        "role": msg.get("role", "unknown"),
                        "content_length": len(str(msg.get("content", ""))),
                        "confidence": msg.get("confidence", "N/A"),
                        "mode": msg.get("mode", "normal")
                    }})
        
        # 채팅 기록 표시
        chat_container = st.container()
        
        with chat_container:
            if not st.session_state.chat_history:
                st.info("👋 안녕하세요! 도시정비사업 관련 질문을 해주세요.")
            else:
                for message in st.session_state.chat_history:
                    self.render_message(message)
        
        # 질의 입력
        st.markdown("---")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "법령 관련 질문을 입력하세요:",
                placeholder="예: 재개발 조합 설립 요건은 무엇인가요?",
                key="user_input"
            )
        
        with col2:
            send_button = st.button("📤 전송", type="primary")
        
        # Enter 키 또는 버튼 클릭 시 처리
        if send_button and user_input.strip():
            self.process_query(user_input.strip())
            # 입력창 초기화를 위해 rerun
            st.rerun()
        
        # 원문 정보 표시 (별도 영역)
        if hasattr(st.session_state, 'show_source_info') and st.session_state.show_source_info:
            st.markdown("---")
            source_info = st.session_state.show_source_info
            self.show_source_document(source_info['law_name'], source_info['article_number'])
            
            # 닫기 버튼
            if st.button("❌ 원문 정보 닫기", key="close_source_info"):
                del st.session_state.show_source_info
                st.rerun()
    
    def render_message(self, message: Dict[str, Any]):
        """개별 메시지 렌더링"""
        if message["role"] == "user":
            # 사용자 메시지를 일반 st.chat_message로 표시
            with st.chat_message("user"):
                st.write(f"👤 **사용자:** {message['content']}")
        
        elif message["role"] == "assistant":
            # AI 응답 메시지
            with st.chat_message("assistant"):
                # 신뢰도 표시
                confidence = message.get("confidence", 0)
                if confidence >= 0.8:
                    confidence_emoji = "🟢"
                elif confidence >= 0.6:
                    confidence_emoji = "🟡"
                else:
                    confidence_emoji = "🔴"
                
                # 메시지 내용 표시
                st.write(f"🤖 **AI 어시스턴트** {confidence_emoji} (신뢰도: {confidence:.2f})")
                st.write(message.get("content", "응답 내용이 없습니다."))
                
                # 모드 표시 (테스트/백업 모드인 경우)
                if message.get("mode") == "demo":
                    st.info("💡 **테스트 모드**: 현재 데모 응답입니다.")
                elif message.get("mode") == "backup":
                    st.info("💡 **백업 모드**: Neo4j 연결 실패로 기본 AI만 사용 중입니다.")
                
                # 출처 정보 표시 (있는 경우)
                if "sources" in message and message["sources"]:
                    st.markdown("**📚 참고 법령 조문:**")
                    # 메시지 고유 ID 생성 (타임스탬프 기반)
                    message_id = message.get('timestamp', str(hash(message.get('content', ''))))
                    for i, source in enumerate(message["sources"][:3], 1):
                        with st.expander(f"{i}. {source.get('law_name', '')} {source.get('article_number', '')}", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**조문:** {source.get('article_number', '')}")
                                st.write(f"**법령:** {source.get('law_name', '')}")
                                st.write(f"**내용:** {source.get('content_preview', '')}")
                                st.write(f"**유사도:** {source.get('similarity_score', 0):.3f}")
                            
                            with col2:
                                # 원문 파일 보기 버튼 - 고유 키 생성
                                law_name = source.get('law_name', '')
                                article_number = source.get('article_number', '')
                                unique_key = f"source_{message_id}_{i}_{hash(law_name + article_number)}"
                                if st.button(f"📄 원문 보기", key=unique_key):
                                    # session state에 저장하여 별도 영역에서 표시
                                    st.session_state.show_source_info = {
                                        'law_name': law_name,
                                        'article_number': article_number
                                    }
                
                # 관련 조문 추천 (있는 경우)
                if "related_articles" in message and message["related_articles"]:
                    st.markdown("**🔗 관련 조문 추천:**")
                    for related in message["related_articles"][:3]:
                        st.info(f"**{related.get('article_number', '')}**: {related.get('content_preview', '')}")
    
    def process_query(self, query: str):
        """사용자 질의 처리"""
        if not st.session_state.system_ready:
            st.error("시스템이 준비되지 않았습니다. 페이지를 새로고침해주세요.")
            return
        
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # 로딩 표시
        with st.spinner("법령 검색 중..."):
            try:
                # RAG 체인이 있는 경우 (그래프 모드)
                if hasattr(st.session_state.rag_chain, 'query_with_sources'):
                    result = st.session_state.rag_chain.query_with_sources(query)
                    
                    # 어시스턴트 응답 추가
                    assistant_message = {
                        "role": "assistant",
                        "content": result["answer"],
                        "confidence": result["confidence"],
                        "sources": result["sources"],
                        "related_articles": result.get("related_articles", []),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    st.session_state.chat_history.append(assistant_message)
                    logger.info(f"그래프 RAG 질의 처리 완료: {query[:50]}...")
                    
                else:
                    # 백업 모드 (기본 Gemini만 사용)
                    try:
                        prompt = f"""당신은 도시정비사업 법령 전문가입니다. 다음 질문에 대해 도시 및 주거환경정비법, 소규모주택정비법 등 관련 법령을 바탕으로 정확하고 자세한 답변을 해주세요.

질문: {query}

답변 시 관련 법령 조문을 명시하고, 구체적이고 실무에 도움이 되는 정보를 제공해주세요."""
                        
                        # 문자열로 직접 호출
                        response = st.session_state.rag_chain.invoke(prompt)
                        
                        # 어시스턴트 응답 추가 (백업 모드)
                        assistant_message = {
                            "role": "assistant",
                            "content": response.content if hasattr(response, 'content') else str(response),
                            "confidence": 0.7,  # 백업 모드 기본 신뢰도
                            "sources": [],
                            "related_articles": [],
                            "mode": "backup",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    except Exception as api_error:
                        # API 키 오류 시 더미 응답 제공
                        logger.error(f"Gemini API 오류: {api_error}")
                        
                        # 도시정비사업 관련 더미 응답 생성
                        dummy_responses = {
                            "재개발": "재개발 조합 설립을 위해서는 도시 및 주거환경정비법 제16조에 따라 토지면적의 3분의 2 이상, 토지소유자 수의 3분의 2 이상의 동의가 필요합니다. 또한 조합설립인가 신청서와 관련 서류를 시장·군수에게 제출해야 합니다.",
                            "소규모": "소규모주택정비법에 따른 소규모재개발사업에서는 현금청산 대상자 중 일정 요건을 충족하는 경우 현금청산에서 제외될 수 있습니다. 구체적으로는 해당 지역 거주기간, 소유 기간 등이 고려됩니다.",
                            "정비사업": "정비사업 시행인가는 도시 및 주거환경정비법 제66조에 따라 사업시행자가 시장·군수에게 신청하며, 관련 서류 검토 후 인가 여부가 결정됩니다.",
                            "가로주택": "가로주택정비사업은 노후·불량건축물이 밀집한 지역에서 소규모로 주거환경을 개선하는 사업으로, 관련 법령에서 정한 요건을 충족해야 합니다.",
                            "빈집": "빈집정비특례법에 따라 장기간 방치된 빈집에 대해서는 특례적인 정비 절차가 적용될 수 있습니다."
                        }
                        
                        # 질의와 관련된 키워드 찾기
                        response_content = "죄송합니다. 현재 AI 서비스에 일시적인 문제가 있습니다."
                        for keyword, response in dummy_responses.items():
                            if keyword in query:
                                response_content = f"[테스트 모드] {response}\n\n※ 현재 테스트 모드로 운영 중입니다. 정확한 법령 정보는 관련 법령을 직접 확인해주세요."
                                break
                        
                        assistant_message = {
                            "role": "assistant",
                            "content": response_content,
                            "confidence": 0.5,  # 더미 모드 신뢰도
                            "sources": [],
                            "related_articles": [],
                            "mode": "demo",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    st.session_state.chat_history.append(assistant_message)
                    logger.info(f"백업/테스트 모드 질의 처리 완료: {query[:50]}...")
                
            except Exception as e:
                st.error(f"질의 처리 중 오류가 발생했습니다: {str(e)}")
                logger.error(f"질의 처리 오류: {e}")
                
                # 기본 에러 응답
                error_message = {
                    "role": "assistant", 
                    "content": "죄송합니다. 현재 시스템에 문제가 있어 답변을 드릴 수 없습니다. 잠시 후 다시 시도해주세요.",
                    "confidence": 0.0,
                    "sources": [],
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.chat_history.append(error_message)
    
    def show_source_document(self, law_name: str, article_number: str):
        """원문 법령 문서 표시 (중첩 Expander 문제 해결)"""
        # 법령명과 파일명 매핑
        law_file_mapping = {
            "도시 및 주거환경정비법": "도시 및 주거환경정비법(법률)(제20955호)(20250520).doc",
            "소규모주택정비법": "빈집 및 소규모주택 정비에 관한 특례법(법률)(제19225호)(20240215).doc",
            "빈집 및 소규모주택 정비에 관한 특례법": "빈집 및 소규모주택 정비에 관한 특례법(법률)(제19225호)(20240215).doc",
            "정비사업 계약업무 처리기준": "정비사업 계약업무 처리기준(국토교통부고시)(제2024-465호)(20240905).doc",
            "서울특별시 도시재정비 촉진을 위한 조례": "서울특별시 도시재정비 촉진을 위한 조례(서울특별시조례)(제9639호)(20250519).doc",
            "용인시 도시 및 주거환정비 조례": "용인시 도시 및 주거환경정비 조례(경기도 용인시조례)(제2553호)(20240925).doc",
            "성남시 도시계획 조례": "성남시 도시계획 조례(경기도 성남시조례)(제4203호)(20250310).doc",
            "안양시 도시계획 조례": "안양시 도시계획 조례(경기도 안양시조례)(제3675호)(20240927).doc"
        }
        
        # 부분 매칭으로 파일 찾기
        matched_file = None
        for law_key, filename in law_file_mapping.items():
            if law_key in law_name or law_name in law_key:
                matched_file = filename
                break
        
        if matched_file:
            file_path = f"data/laws/{matched_file}"
            
            # 파일 존재 확인
            if os.path.exists(file_path):
                # Expander 대신 직접 컨테이너 사용 (중첩 방지)
                st.markdown("---")
                st.markdown(f"### 📄 **{law_name}** 원문 정보")
                st.markdown(f"**🔍 찾고 있는 조문:** {article_number}")
                st.markdown(f"**📁 파일명:** {matched_file}")
                
                # 파일 다운로드 링크 제공
                try:
                    with open(file_path, 'rb') as file:
                        file_data = file.read()
                        st.download_button(
                            label="📥 원문 파일 다운로드",
                            data=file_data,
                            file_name=matched_file,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"download_{hash(law_name + article_number)}"
                        )
                except Exception as e:
                    st.error(f"파일 읽기 오류: {e}")
                
                # 관련 조문 정보 표시
                st.info(f"🎯 이 법령의 {article_number} 관련 정보를 찾고 계신가요? 원문 파일을 다운로드하여 상세한 조문 내용을 확인하실 수 있습니다.")
                
                # 관련 질의 제안
                if article_number:
                    suggested_queries = [
                        f"{law_name} {article_number}의 상세 내용은?",
                        f"{article_number}와 관련된 다른 조문들은?",
                        f"{law_name}의 {article_number} 시행규칙은?"
                    ]
                    
                    st.markdown("**💡 관련 질의 제안:**")
                    col1, col2, col3 = st.columns(3)
                    
                    for idx, query in enumerate(suggested_queries):
                        unique_key = f"suggest_{hash(law_name + article_number + str(idx))}"
                        with [col1, col2, col3][idx]:
                            if st.button(query, key=unique_key, help="클릭하여 관련 질의하기"):
                                st.session_state.suggested_query = query
                                # 원문 정보 닫기
                                if hasattr(st.session_state, 'show_source_info'):
                                    del st.session_state.show_source_info
                                st.rerun()
            else:
                st.error(f"파일을 찾을 수 없습니다: {file_path}")
        else:
            st.warning(f"'{law_name}'에 해당하는 원문 파일을 찾을 수 없습니다.")
            
            # 사용 가능한 법령 목록 표시
            st.markdown("**📚 현재 사용 가능한 법령:**")
            for law in law_file_mapping.keys():
                st.markdown(f"- {law}")
    
    def get_file_content_preview(self, file_path: str, max_chars: int = 500) -> str:
        """파일 내용 미리보기 (텍스트 파일의 경우)"""
        try:
            # .txt 파일인 경우에만 미리보기 제공
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > max_chars:
                        return content[:max_chars] + "..."
                    return content
            else:
                return "파일 내용 미리보기는 텍스트 파일만 지원됩니다."
        except Exception as e:
            return f"파일 읽기 오류: {e}"
    
    def export_chat_history(self):
        """채팅 기록 내보내기"""
        if not st.session_state.chat_history:
            st.warning("내보낼 채팅 기록이 없습니다.")
            return
        
        # JSON 형태로 변환
        export_data = {
            "session_info": {
                "export_time": datetime.now().isoformat(),
                "total_messages": len(st.session_state.chat_history)
            },
            "chat_history": st.session_state.chat_history
        }
        
        # 다운로드 링크 생성
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 JSON 다운로드",
            data=json_str,
            file_name=f"legal_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def run(self):
        """어시스턴트 실행"""
        # 시스템 구성 요소 로드
        if not st.session_state.system_ready:
            with st.spinner("시스템 초기화 중..."):
                graph_manager, rag_chain, ready = self.load_components()
                
                if ready:
                    st.session_state.graph_manager = graph_manager
                    st.session_state.rag_chain = rag_chain
                    st.session_state.system_ready = True
                    st.success("시스템 초기화 완료!")
                    st.rerun()
                else:
                    st.error("시스템 초기화에 실패했습니다. 설정을 확인해주세요.")
                    st.stop()
        
        # 헤더 렌더링
        self.render_header()
        
        # 안정적인 레이아웃 구성
        # 사이드바를 진짜 사이드바로 이동
        with st.sidebar:
            self.render_sidebar()
        
        # 메인 컨테이너
        main_container = st.container()
        with main_container:
            # 메인 채팅 인터페이스
            self.render_chat_interface()


def main():
    """메인 함수"""
    # 페이지 설정을 가장 먼저 수행
    st.set_page_config(
        page_title="도시정비 법령 전문 AI",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
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
    """, unsafe_allow_html=True)
    
    try:
        assistant = LegalAssistant()
        assistant.run()
        
    except Exception as e:
        st.error(f"어플리케이션 실행 중 오류가 발생했습니다: {str(e)}")
        logger.error(f"어플리케이션 오류: {e}")


if __name__ == "__main__":
    main() 