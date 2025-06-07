#!/usr/bin/env python3
"""
새로운 파서 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.document_processor import LegalDocumentProcessor

def test_new_parsers():
    print("🧪 새로운 파서 테스트 시작...")
    
    # 그래프 관리자 초기화
    graph_manager = LegalGraphManager()
    
    # 문서 처리기 초기화
    processor = LegalDocumentProcessor(graph_manager)
    
    # 1. HWP 파일 테스트 (다른 파일로 변경)
    print("\n1️⃣ HWP 파일 테스트...")
    hwp_file = "data/laws/별표 3 청렴서약서(성남시 도시계획 조례).hwp"
    hwp_result = processor.process_hwp_document(hwp_file, "seongnam_ordinance_test")
    print(f"HWP 처리 결과: {hwp_result}")
    
    # 2. DOC 파일 테스트 (다른 파일로 변경)
    print("\n2️⃣ DOC 파일 테스트...")
    doc_file = "data/laws/안양시 도시계획 조례(경기도 안양시조례)(제3675호)(20240927).doc"
    doc_result = processor.process_doc_document(doc_file, "anyang_ordinance_test")
    print(f"DOC 처리 결과: {doc_result}")
    
    # 3. 현재 Neo4j 상태 확인
    print("\n3️⃣ 현재 Neo4j 상태 확인...")
    with graph_manager.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        print("Neo4j 노드 현황:")
        for record in result:
            print(f"  {record['labels']}: {record['count']}개")
    
    # 연결 종료
    graph_manager.close()
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_new_parsers() 