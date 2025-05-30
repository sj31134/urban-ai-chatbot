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

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.graph.legal_graph import LegalGraphManager
from src.rag.legal_rag_chain import LegalRAGChain
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

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
    
    @st.cache_resource
    def load_components(_self):
        """시스템 구성 요소 로드 (캐시 활용)"""
        try:
            # Neo4j 그래프 관리자 초기화
            graph_manager = LegalGraphManager()
            
            # RAG 체인 초기화
            rag_chain = LegalRAGChain(graph_manager)
            
            return graph_manager, rag_chain, True
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
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
        # 채팅 기록 표시
        chat_container = st.container()
        
        with chat_container:
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
            st.rerun()
    
    def render_message(self, message: Dict[str, Any]):
        """개별 메시지 렌더링"""
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 사용자:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        
        elif message["role"] == "assistant":
            # 신뢰도에 따른 CSS 클래스
            confidence = message.get("confidence", 0)
            if confidence >= 0.8:
                confidence_class = "confidence-high"
                confidence_emoji = "🟢"
            elif confidence >= 0.6:
                confidence_class = "confidence-medium"
                confidence_emoji = "🟡"
            else:
                confidence_class = "confidence-low"
                confidence_emoji = "🔴"
            
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 AI 어시스턴트:</strong>
                <span class="{confidence_class}">{confidence_emoji} 신뢰도: {confidence:.2f}</span><br><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # 출처 정보 표시
            if "sources" in message and message["sources"]:
                st.markdown("**📚 참고 법령 조문:**")
                for i, source in enumerate(message["sources"][:3], 1):
                    with st.expander(f"{i}. {source.get('law_name', '')} {source.get('article_number', '')}", expanded=False):
                        st.markdown(f"""
                        <div class="source-box">
                            <strong>조문:</strong> {source.get('article_number', '')}<br>
                            <strong>법령:</strong> {source.get('law_name', '')}<br>
                            <strong>내용:</strong> {source.get('content_preview', '')}<br>
                            <strong>유사도:</strong> {source.get('similarity_score', 0):.3f}
                        </div>
                        """, unsafe_allow_html=True)
            
            # 관련 조문 추천
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
                # RAG 체인 실행
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
                
                # 로그 기록
                logger.info(f"질의 처리 완료: {query[:50]}... (신뢰도: {result['confidence']})")
                
            except Exception as e:
                st.error(f"질의 처리 중 오류가 발생했습니다: {str(e)}")
                logger.error(f"질의 처리 오류: {e}")
    
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
        # 페이지 설정
        self.setup_page_config()
        
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
        
        # 레이아웃 구성
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 메인 채팅 인터페이스
            self.render_chat_interface()
        
        with col2:
            # 사이드바
            self.render_sidebar()


def main():
    """메인 함수"""
    try:
        assistant = LegalAssistant()
        assistant.run()
        
    except Exception as e:
        st.error(f"어플리케이션 실행 중 오류가 발생했습니다: {str(e)}")
        logger.error(f"어플리케이션 오류: {e}")


if __name__ == "__main__":
    main() 