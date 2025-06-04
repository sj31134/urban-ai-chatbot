#!/usr/bin/env python3
"""
텍스트 추출 디버깅 스크립트
"""

from src.rag.document_processor import LegalDocumentProcessor
from src.graph.legal_graph import LegalGraphManager
import re

def debug_text_extraction():
    print("🔍 텍스트 추출 디버깅 시작...")
    
    graph = LegalGraphManager()
    processor = LegalDocumentProcessor(graph)
    
    # HWP 파일 텍스트 분석
    print("\n1️⃣ HWP 파일 텍스트 분석:")
    hwp_file = 'data/laws/[별표 8] 일반상업지역에서 건축할 수 없는 건축물(안양시 도시계획 조례).hwp'
    hwp_text = processor._extract_hwp_text(hwp_file)
    
    print(f"텍스트 길이: {len(hwp_text)} 문자")
    print("첫 500문자:")
    print(repr(hwp_text[:500]))
    print()
    
    # 조문 패턴 검색
    article_pattern = re.compile(r'제(\d+)조')
    matches = article_pattern.findall(hwp_text)
    print(f"발견된 조문 수: {len(matches)}")
    print(f"조문 예시: {matches[:5]}")
    
    # 다른 패턴들도 확인
    print("\n📋 기타 패턴 검색:")
    print(f"'조례' 키워드: {hwp_text.count('조례')}번")
    print(f"'별표' 키워드: {hwp_text.count('별표')}번")
    print(f"'건축물' 키워드: {hwp_text.count('건축물')}번")
    
    # DOC 파일도 동일하게 분석
    print("\n2️⃣ DOC 파일 텍스트 분석:")
    doc_file = 'data/laws/서울특별시 도시재정비 촉진을 위한 조례(서울특별시조례)(제9639호)(20250519).doc'
    doc_text = processor._extract_doc_text(doc_file)
    
    print(f"텍스트 길이: {len(doc_text)} 문자")
    print("첫 500문자:")
    print(repr(doc_text[:500]))
    print()
    
    # 조문 패턴 검색
    matches = article_pattern.findall(doc_text)
    print(f"발견된 조문 수: {len(matches)}")
    print(f"조문 예시: {matches[:5]}")
    
    graph.close()
    print("\n✅ 디버깅 완료!")

if __name__ == "__main__":
    debug_text_extraction() 