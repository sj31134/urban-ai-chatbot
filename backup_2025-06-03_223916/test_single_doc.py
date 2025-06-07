#!/usr/bin/env python3
"""
단일 DOC 파일 처리 테스트
"""

from src.rag.document_processor import LegalDocumentProcessor
from src.graph.legal_graph import LegalGraphManager

def test_single_doc():
    print("📄 단일 DOC 파일 처리 테스트...")
    
    graph = LegalGraphManager()
    processor = LegalDocumentProcessor(graph)
    
    # DOC 파일 처리
    doc_file = 'data/laws/서울특별시 도시재정비 촉진을 위한 조례(서울특별시조례)(제9639호)(20250519).doc'
    print(f"처리 파일: {doc_file}")
    
    result = processor.process_doc_document(doc_file, 'seoul_ordinance')
    print(f"처리 결과: {result}")
    
    # Neo4j 상태 확인
    print("\n📊 Neo4j 상태 확인:")
    node_result = graph.execute_query('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
    for r in node_result:
        print(f"  {r['labels']}: {r['count']}개")
    
    # 조문 샘플 확인
    if result.get('success', False):
        print("\n📋 조문 샘플 확인:")
        article_result = graph.execute_query('MATCH (a:Article) RETURN a.article_number, a.content LIMIT 3')
        for r in article_result:
            print(f"  {r['a.article_number']}: {r['a.content'][:100]}...")
    
    graph.close()
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_single_doc() 