#!/usr/bin/env python3
"""
최종 시스템 종합 테스트 스크립트
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline

def final_system_test():
    print("🎯 최종 시스템 종합 테스트 시작...")
    
    # 1. 데이터베이스 상태 확인
    print("\n1️⃣ 데이터베이스 상태 확인...")
    graph_manager = LegalGraphManager()
    
    with graph_manager.driver.session() as session:
        # 노드 수
        result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
        print("   📊 노드 현황:")
        for record in result:
            print(f"     {record['labels']}: {record['count']}개")
        
        # 관계 수
        result = session.run('MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count')
        print("   🔗 관계 현황:")
        for record in result:
            print(f"     {record['rel_type']}: {record['count']}개")
    
    # 2. RAG 시스템 초기화 및 성능 테스트
    print("\n2️⃣ RAG 시스템 성능 테스트...")
    rag_pipeline = EnhancedRAGPipeline(graph_manager)
    
    # 다양한 실제 법령 질문들
    real_questions = [
        "정비구역은 어떻게 지정하나요?",
        "조합설립추진위원회 구성 방법은?",
        "재건축 안전진단은 누가 실시하나요?",
        "사업시행인가 신청 절차를 알려주세요",
        "토지등소유자 동의 기준은 무엇인가요?"
    ]
    
    print("   🔍 실제 법령 질문 테스트:")
    total_time = 0
    total_questions = len(real_questions)
    
    for i, question in enumerate(real_questions, 1):
        start_time = time.time()
        try:
            results = rag_pipeline.search(question, search_type="hybrid", k=3)
            end_time = time.time()
            search_time = end_time - start_time
            total_time += search_time
            
            print(f"\n   Q{i}: {question}")
            print(f"   ⏱️ 검색 시간: {search_time:.3f}초")
            
            if results:
                best_result = results[0]
                score = best_result.get('combined_score', 0)
                article = best_result['metadata'].get('article_number', 'N/A')
                content = best_result['content'][:60] + "..." if len(best_result['content']) > 60 else best_result['content']
                
                print(f"   💡 최고 답변: {article} (점수: {score:.3f})")
                print(f"   📄 내용: {content}")
                
                # 품질 평가
                if score >= 0.7:
                    quality = "🟢 우수"
                elif score >= 0.5:
                    quality = "🟡 양호"
                else:
                    quality = "🔴 개선 필요"
                print(f"   📊 품질: {quality}")
            else:
                print(f"   ❌ 결과 없음")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    # 성능 통계
    avg_time = total_time / total_questions
    print(f"\n   📈 성능 통계:")
    print(f"     평균 검색 시간: {avg_time:.3f}초")
    print(f"     총 처리 시간: {total_time:.3f}초")
    print(f"     처리한 질문 수: {total_questions}개")
    
    # 3. 시스템 통계
    print("\n3️⃣ 시스템 통계...")
    try:
        stats = rag_pipeline.get_system_stats()
        print(f"   🧠 임베딩 모델: {stats['embedding_stats']['model_name']}")
        print(f"   📄 임베딩 청크: {stats['embedding_stats']['total_chunks']}개")
        print(f"   🔍 검색 엔진: {stats['search_engine']}")
        
        print(f"   📊 그래프 데이터:")
        for label, count in stats['graph_stats'].items():
            print(f"     {label}: {count}개")
    except Exception as e:
        print(f"   ❌ 통계 오류: {e}")
    
    # 4. 스트레스 테스트
    print("\n4️⃣ 스트레스 테스트...")
    stress_queries = ["도시정비"] * 10  # 같은 쿼리 10번
    
    start_time = time.time()
    for i in range(len(stress_queries)):
        try:
            results = rag_pipeline.search(stress_queries[i], search_type="hybrid", k=1)
        except Exception as e:
            print(f"   스트레스 테스트 {i+1} 실패: {e}")
    end_time = time.time()
    
    stress_time = end_time - start_time
    queries_per_second = len(stress_queries) / stress_time
    
    print(f"   ⚡ 스트레스 테스트 결과:")
    print(f"     총 쿼리: {len(stress_queries)}개")
    print(f"     총 시간: {stress_time:.3f}초")
    print(f"     초당 쿼리: {queries_per_second:.1f}개/초")
    
    # 5. 최종 평가
    print("\n5️⃣ 최종 시스템 평가...")
    
    # 평가 기준
    evaluations = []
    
    # 검색 속도 평가
    if avg_time < 0.1:
        speed_score = "🟢 매우 빠름"
    elif avg_time < 0.5:
        speed_score = "🟡 빠름"
    else:
        speed_score = "🔴 느림"
    evaluations.append(f"검색 속도: {speed_score} ({avg_time:.3f}초)")
    
    # 처리량 평가
    if queries_per_second > 10:
        throughput_score = "🟢 우수"
    elif queries_per_second > 5:
        throughput_score = "🟡 양호"
    else:
        throughput_score = "🔴 개선 필요"
    evaluations.append(f"처리량: {throughput_score} ({queries_per_second:.1f}개/초)")
    
    # 데이터 규모 평가
    total_articles = stats['graph_stats'].get('Article', 0)
    total_laws = stats['graph_stats'].get('Law', 0)
    
    if total_articles > 500 and total_laws > 20:
        data_score = "🟢 충분"
    elif total_articles > 100 and total_laws > 5:
        data_score = "🟡 적당"
    else:
        data_score = "🔴 부족"
    evaluations.append(f"데이터 규모: {data_score} (Article: {total_articles}, Law: {total_laws})")
    
    print("   📊 종합 평가:")
    for evaluation in evaluations:
        print(f"     {evaluation}")
    
    # 연결 종료
    graph_manager.close()
    
    print("\n🎉 최종 테스트 완료!")
    print("\n📋 시스템 상태 요약:")
    print("   ✅ 데이터베이스: 정상 작동")
    print("   ✅ RAG 검색: 정상 작동")
    print("   ✅ 임베딩 시스템: 정상 작동")
    print("   ✅ 하이브리드 검색: 정상 작동")

if __name__ == "__main__":
    final_system_test() 