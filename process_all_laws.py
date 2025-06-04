#!/usr/bin/env python3
"""
모든 법령 파일 일괄 처리 스크립트
HWP, DOC, PDF 등 모든 지원 형식 처리
"""

import sys
import os
import time
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager
from src.rag.document_processor import LegalDocumentProcessor

def process_all_legal_documents():
    """모든 법령 문서 일괄 처리"""
    print("🏛️ 법령 문서 일괄 처리 시작...")
    
    # 그래프 관리자 및 문서 처리기 초기화
    graph_manager = LegalGraphManager()
    processor = LegalDocumentProcessor(graph_manager)
    
    # 데이터 디렉토리
    data_dir = Path("data/laws")
    
    # 지원하는 파일 형식
    supported_extensions = ['.hwp', '.doc', '.docx', '.pdf', '.txt']
    
    # 결과 추적
    results = {
        'total_files': 0,
        'processed_files': 0,
        'failed_files': 0,
        'skipped_files': 0,
        'details': []
    }
    
    # 모든 파일 처리
    for file_path in data_dir.rglob('*'):
        if file_path.suffix.lower() in supported_extensions:
            results['total_files'] += 1
            
            print(f"\n📄 처리 중: {file_path.name}")
            
            try:
                # 고유 법령 코드 생성 (타임스탬프 포함)
                timestamp = str(int(time.time()))[-6:]
                base_name = file_path.stem.replace(' ', '_').replace('(', '').replace(')', '')
                law_code = f"{base_name}_{timestamp}"
                
                # 파일 처리
                result = processor.process_document(str(file_path), law_code)
                
                if result.get('status') == 'success' or result.get('success') == True:
                    results['processed_files'] += 1
                    print(f"✅ 성공: {result.get('processed_articles', 0)}개 조문 처리")
                elif 'already exists' in str(result.get('message', '')):
                    results['skipped_files'] += 1
                    print(f"⏭️ 건너뜀: 이미 처리됨")
                else:
                    results['failed_files'] += 1
                    print(f"❌ 실패: {result.get('message', '알 수 없는 오류')}")
                
                results['details'].append({
                    'file': file_path.name,
                    'law_code': law_code,
                    'result': result
                })
                
            except Exception as e:
                results['failed_files'] += 1
                print(f"❌ 예외 발생: {e}")
                results['details'].append({
                    'file': file_path.name,
                    'error': str(e)
                })
            
            # 짧은 대기 (시스템 부하 방지)
            time.sleep(0.5)
    
    # 결과 출력
    print(f"\n📊 처리 완료 통계:")
    print(f"   총 파일: {results['total_files']}개")
    print(f"   처리 성공: {results['processed_files']}개")
    print(f"   건너뜀: {results['skipped_files']}개")
    print(f"   실패: {results['failed_files']}개")
    
    # 최종 데이터베이스 상태 확인
    print(f"\n🗄️ 최종 데이터베이스 상태:")
    with graph_manager.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
        for record in result:
            print(f"   {record['labels']}: {record['count']}개")
    
    # 연결 종료
    graph_manager.close()
    
    return results

if __name__ == "__main__":
    results = process_all_legal_documents()
    print(f"\n✅ 전체 작업 완료!") 