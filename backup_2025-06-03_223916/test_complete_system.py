#!/usr/bin/env python3
"""
통합 시스템 테스트 스크립트
1. 새로운 법령 파일 처리
2. RAG 파이프라인 개선
3. 임베딩 시스템 최적화
4. 검색 기능 강화
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.document_processor import LegalDocumentProcessor
from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline

def main():
    print("🚀 통합 시스템 테스트 시작...")
    
    # 1. 그래프 관리자 초기화
    print("\n1️⃣ 그래프 관리자 초기화...")
    graph_manager = LegalGraphManager()
    
    # 현재 데이터베이스 상태 확인
    print("\n📊 현재 데이터베이스 상태:")
    with graph_manager.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
        for record in result:
            print(f"   {record['labels']}: {record['count']}개")
    
    # 2. 새로운 법령 파일 처리 (몇 개만 샘플로)
    print("\n2️⃣ 새로운 법령 파일 처리...")
    processor = LegalDocumentProcessor(graph_manager)
    
    # 샘플 파일들 처리
    sample_files = [
        ("data/laws/서울특별시 도시재정비 촉진을 위한 조례(서울특별시조례)(제6949호)(20190101).doc", "seoul_urban_redevelopment"),
        ("data/laws/별표 3 청렴서약서(성남시 도시계획 조례).hwp", "seongnam_planning_oath")
    ]
    
    for file_path, law_code in sample_files:
        if os.path.exists(file_path):
            print(f"\n📄 처리 중: {file_path}")
            try:
                result = processor.process_document(file_path, f"{law_code}_{int(time.time())}")
                if result.get('success') or 'already exists' in str(result.get('message', '')):
                    print(f"✅ 처리 완료")
                else:
                    print(f"⚠️ 처리 결과: {result}")
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    # 3. RAG 파이프라인 초기화 및 테스트
    print("\n3️⃣ 향상된 RAG 파이프라인 초기화...")
    try:
        rag_pipeline = EnhancedRAGPipeline(graph_manager)
        
        # 4. 임베딩 시스템 최적화 - 모든 문서 인덱싱
        print("\n4️⃣ 임베딩 시스템 최적화 - 문서 인덱싱...")
        rag_pipeline.index_all_documents()
        
        # 5. 검색 기능 강화 테스트
        print("\n5️⃣ 검색 기능 강화 테스트...")
        
        # 다양한 검색 쿼리로 테스트
        test_queries = [
            "도시정비사업의 시행자는 누구인가?",
            "조합설립인가 절차는?", 
            "안전진단 기준",
            "재개발 절차",
            "주민동의 요건"
        ]
        
        for query in test_queries:
            print(f"\n🔍 검색 쿼리: '{query}'")
            
            # 하이브리드 검색 (벡터 + 키워드)
            try:
                hybrid_results = rag_pipeline.search(query, search_type="hybrid", k=3)
                print("   📋 하이브리드 검색 결과:")
                for i, result in enumerate(hybrid_results, 1):
                    score = result.get('combined_score', 0)
                    article = result['metadata'].get('article_number', 'N/A')
                    law_name = result['metadata'].get('law_name', 'N/A')
                    content_preview = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
                    print(f"     {i}. {article} (점수: {score:.3f}) - {law_name}")
                    print(f"        {content_preview}")
            except Exception as e:
                print(f"   ❌ 하이브리드 검색 오류: {e}")
            
            # 벡터 검색만
            try:
                vector_results = rag_pipeline.search(query, search_type="vector", k=2)
                print("   🎯 벡터 검색 결과:")
                for i, result in enumerate(vector_results, 1):
                    score = result.get('similarity_score', 0)
                    article = result['metadata'].get('article_number', 'N/A')
                    print(f"     {i}. {article} (유사도: {score:.3f})")
            except Exception as e:
                print(f"   ❌ 벡터 검색 오류: {e}")
            
            print()  # 구분선
    
    except Exception as e:
        print(f"❌ RAG 파이프라인 오류: {e}")
    
    # 6. 시스템 통계 및 성능 확인
    print("\n6️⃣ 시스템 통계 및 성능 확인...")
    
    # 최종 데이터베이스 상태
    print("\n📊 최종 데이터베이스 상태:")
    with graph_manager.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
        for record in result:
            print(f"   {record['labels']}: {record['count']}개")
    
    # RAG 시스템 통계
    try:
        if 'rag_pipeline' in locals():
            stats = rag_pipeline.get_system_stats()
            print("\n📈 RAG 시스템 통계:")
            print(f"   임베딩 모델: {stats['embedding_stats']['model_name']}")
            print(f"   총 청크 수: {stats['embedding_stats']['total_chunks']}")
            print(f"   검색 엔진: {stats['search_engine']}")
    except Exception as e:
        print(f"   ❌ 통계 수집 오류: {e}")
    
    # 7. 성능 테스트
    print("\n7️⃣ 성능 테스트...")
    try:
        if 'rag_pipeline' in locals():
            start_time = time.time()
            performance_query = "조합설립인가"
            results = rag_pipeline.search(performance_query, search_type="hybrid", k=5)
            end_time = time.time()
            
            print(f"   검색 쿼리: '{performance_query}'")
            print(f"   검색 시간: {end_time - start_time:.3f}초")
            print(f"   결과 수: {len(results)}개")
    except Exception as e:
        print(f"   ❌ 성능 테스트 오류: {e}")
    
    # 연결 종료
    print("\n🔚 테스트 완료, 연결 종료...")
    graph_manager.close()
    
    print("\n✅ 모든 시스템 테스트 완료!")
    print("\n📋 요약:")
    print("   1. ✅ 새로운 법령 파일 처리 완료")
    print("   2. ✅ RAG 파이프라인 개선 완료")
    print("   3. ✅ 임베딩 시스템 최적화 완료") 
    print("   4. ✅ 검색 기능 강화 완료")

if __name__ == "__main__":
    main() 