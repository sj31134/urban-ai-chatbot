#!/usr/bin/env python3
"""
RAG 검색 기능 테스트 스크립트
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.enhanced_rag_pipeline import EnhancedRAGPipeline

def test_rag_search():
    print("🔍 RAG 검색 기능 테스트 시작...")
    
    # 1. 시스템 초기화
    print("\n1️⃣ 시스템 초기화...")
    graph_manager = LegalGraphManager()
    rag_pipeline = EnhancedRAGPipeline(graph_manager)
    
    # 2. 간단한 검색 테스트
    print("\n2️⃣ 간단한 검색 테스트...")
    
    test_queries = [
        "도시정비사업이란?",
        "조합설립인가 절차",
        "안전진단 기준"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: '{query}'")
        
        start_time = time.time()
        try:
            results = rag_pipeline.search(query, search_type="hybrid", k=2)
            end_time = time.time()
            
            print(f"   ⏱️ 검색 시간: {end_time - start_time:.3f}초")
            print(f"   📋 결과 ({len(results)}개):")
            
            for j, result in enumerate(results, 1):
                score = result.get('combined_score', 0)
                article = result['metadata'].get('article_number', 'N/A')
                content = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
                print(f"     {j}. {article} (점수: {score:.3f})")
                print(f"        {content}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    # 3. 시스템 통계
    print(f"\n3️⃣ 시스템 통계...")
    try:
        stats = rag_pipeline.get_system_stats()
        print(f"   🧠 임베딩 모델: {stats['embedding_stats']['model_name']}")
        print(f"   📄 총 청크 수: {stats['embedding_stats']['total_chunks']}")
        print(f"   🔍 검색 엔진: {stats['search_engine']}")
    except Exception as e:
        print(f"   ❌ 통계 오류: {e}")
    
    graph_manager.close()
    print(f"\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_rag_search() 