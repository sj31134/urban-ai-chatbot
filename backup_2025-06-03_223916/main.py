#!/usr/bin/env python3
"""
도시정비사업 법령 전문 AI 챗봇 - 메인 애플리케이션
"""

import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline


class UrbanLegalRAGChatbot:
    """도시정비사업 법령 전문 AI 챗봇"""
    
    def __init__(self):
        """챗봇 초기화"""
        self.graph_manager = None
        self.rag_pipeline = None
        self.session_start_time = datetime.now()
        self.query_count = 0
        
    def initialize(self):
        """시스템 초기화"""
        print("🤖 도시정비사업 법령 전문 AI 챗봇을 시작합니다...")
        print("📚 시스템 초기화 중...")
        
        try:
            # 그래프 관리자 초기화
            print("   🔗 Neo4j 데이터베이스 연결 중...")
            self.graph_manager = LegalGraphManager()
            
            # RAG 파이프라인 초기화
            print("   🧠 RAG 검색 시스템 초기화 중...")
            self.rag_pipeline = EnhancedRAGPipeline(self.graph_manager)
            
            # 시스템 상태 확인
            stats = self.rag_pipeline.get_system_stats()
            
            print("\n✅ 시스템 초기화 완료!")
            print(f"   📄 법령 데이터: {stats['graph_stats'].get('Law', 0)}개 법령, {stats['graph_stats'].get('Article', 0)}개 조문")
            print(f"   🧠 임베딩: {stats['embedding_stats']['total_chunks']}개 청크")
            print(f"   🔍 검색 엔진: {stats['search_engine']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 시스템 초기화 실패: {e}")
            return False
    
    def show_welcome_message(self):
        """환영 메시지 출력"""
        print("\n" + "="*60)
        print("🏛️  도시정비사업 법령 전문 AI 챗봇")
        print("="*60)
        print("📖 도시정비사업 관련 법령에 대해 무엇이든 물어보세요!")
        print("\n💡 예시 질문:")
        print("   • 도시정비사업이란 무엇인가요?")
        print("   • 조합설립인가 절차를 알려주세요")
        print("   • 재건축 안전진단 기준은?")
        print("   • 주민동의 요건이 궁금해요")
        print("   • 정비구역 지정 절차는?")
        print("\n📝 명령어:")
        print("   • 'quit', 'exit', '종료': 챗봇 종료")
        print("   • 'help', '도움말': 도움말 보기")
        print("   • 'stats', '통계': 시스템 통계 보기")
        print("="*60)
    
    def search_and_respond(self, query: str, search_type: str = "hybrid", k: int = 3):
        """질문 검색 및 응답 생성"""
        try:
            start_time = time.time()
            
            # RAG 검색 수행
            results = self.rag_pipeline.search(query, search_type=search_type, k=k)
            
            end_time = time.time()
            search_time = end_time - start_time
            
            # 응답 생성
            if results:
                print(f"\n🔍 검색 결과 (검색 시간: {search_time:.3f}초):")
                print("-" * 50)
                
                for i, result in enumerate(results, 1):
                    score = result.get('combined_score', result.get('similarity_score', 0))
                    article = result['metadata'].get('article_number', 'N/A')
                    law_name = result['metadata'].get('law_name', 'N/A')
                    content = result['content']
                    
                    print(f"\n📋 {i}. {article} (관련도: {score:.1%})")
                    if law_name != 'N/A':
                        print(f"   📚 출처: {law_name}")
                    
                    # 내용을 적절히 나누어서 표시
                    if len(content) > 200:
                        print(f"   📄 내용: {content[:200]}...")
                        print(f"   💬 더 보기: {content[200:400]}...")
                    else:
                        print(f"   📄 내용: {content}")
                    
                    if i < len(results):
                        print()
                
                # 추가 정보 제공
                if len(results) > 1:
                    print(f"\n💡 총 {len(results)}개의 관련 조문을 찾았습니다.")
                    best_score = results[0].get('combined_score', 0)
                    if best_score >= 0.8:
                        confidence = "매우 높음"
                    elif best_score >= 0.6:
                        confidence = "높음"
                    elif best_score >= 0.4:
                        confidence = "보통"
                    else:
                        confidence = "낮음"
                    print(f"📊 답변 신뢰도: {confidence}")
                
            else:
                print(f"\n❌ 죄송합니다. '{query}'에 대한 관련 법령을 찾을 수 없습니다.")
                print("💡 다른 키워드로 다시 질문해보세요.")
                print("   예: '도시정비', '조합설립', '안전진단', '재개발' 등")
            
            self.query_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 검색 중 오류가 발생했습니다: {e}")
            return False
    
    def show_statistics(self):
        """시스템 통계 표시"""
        try:
            stats = self.rag_pipeline.get_system_stats()
            session_time = datetime.now() - self.session_start_time
            
            print("\n📊 시스템 통계:")
            print("-" * 40)
            print(f"🧠 임베딩 모델: {stats['embedding_stats']['model_name']}")
            print(f"📄 임베딩 청크: {stats['embedding_stats']['total_chunks']}개")
            print(f"🔍 검색 엔진: {stats['search_engine']}")
            print(f"📚 법령 데이터:")
            for label, count in stats['graph_stats'].items():
                print(f"   {label}: {count}개")
            print(f"⏱️ 세션 시간: {str(session_time).split('.')[0]}")
            print(f"🔍 질문 횟수: {self.query_count}회")
            
        except Exception as e:
            print(f"❌ 통계 조회 오류: {e}")
    
    def show_help(self):
        """도움말 표시"""
        print("\n📖 도움말:")
        print("-" * 40)
        print("🔍 검색 팁:")
        print("   • 구체적인 키워드 사용 (예: '조합설립인가', '안전진단')")
        print("   • 질문 형태로 입력 (예: '~은 무엇인가요?', '~는 어떻게 하나요?')")
        print("   • 법령 조문 번호로 검색 (예: '제12조', '제3조')")
        print("\n💡 주요 키워드:")
        print("   • 도시정비사업, 재개발, 재건축")
        print("   • 조합설립, 추진위원회")
        print("   • 안전진단, 정비계획")
        print("   • 사업시행인가, 주민동의")
        print("   • 정비구역, 토지등소유자")
    
    def run(self):
        """챗봇 실행"""
        # 시스템 초기화
        if not self.initialize():
            print("❌ 시스템 초기화에 실패했습니다. 프로그램을 종료합니다.")
            return
        
        # 환영 메시지
        self.show_welcome_message()
        
        # 메인 루프
        try:
            while True:
                print("\n" + "="*60)
                user_input = input("🤖 질문을 입력하세요: ").strip()
                
                if not user_input:
                    continue
                
                # 종료 명령어
                if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                    print("\n👋 도시정비사업 법령 전문 AI 챗봇을 종료합니다.")
                    print(f"📊 총 {self.query_count}개의 질문에 답변했습니다.")
                    break
                
                # 도움말 명령어
                elif user_input.lower() in ['help', '도움말', 'h']:
                    self.show_help()
                    continue
                
                # 통계 명령어
                elif user_input.lower() in ['stats', '통계', 's']:
                    self.show_statistics()
                    continue
                
                # 일반 질문 처리
                else:
                    print(f"\n🔍 '{user_input}'에 대해 검색 중...")
                    self.search_and_respond(user_input)
        
        except KeyboardInterrupt:
            print("\n\n👋 사용자가 프로그램을 중단했습니다.")
        
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        
        finally:
            # 리소스 정리
            if self.graph_manager:
                self.graph_manager.close()
                print("🔗 데이터베이스 연결을 종료했습니다.")


def main():
    """메인 함수"""
    chatbot = UrbanLegalRAGChatbot()
    chatbot.run()


if __name__ == "__main__":
    main() 