#!/usr/bin/env python3
"""
도시정비사업 법령 문서 일괄 처리 스크립트
data/laws 디렉토리의 모든 법령 문서를 Neo4j 그래프 데이터베이스에 로드
"""

# 필요한 라이브러리 import
import os  # 운영체제 관련 기능
import sys  # 시스템 관련 기능
import logging  # 로그 기록
from pathlib import Path  # 경로 처리
from datetime import datetime  # 날짜/시간 처리
from typing import List, Dict, Any  # 타입 힌트

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 디렉토리
sys.path.insert(0, project_root)  # 시스템 경로에 추가

# 프로젝트 내부 모듈 import
from src.graph.legal_graph import LegalGraphManager  # Neo4j 그래프 관리자
from src.rag.document_processor import LegalDocumentProcessor  # 문서 처리기
from dotenv import load_dotenv  # 환경변수 로드

# 환경변수 로드
load_dotenv()  # .env 파일에서 환경변수 읽기

# 로깅 설정
logging.basicConfig(  # 로깅 기본 설정
    level=logging.INFO,  # INFO 레벨 로깅
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 로그 형식
    handlers=[  # 핸들러 설정
        logging.FileHandler('logs/document_processing.log', encoding='utf-8'),  # 파일 로그
        logging.StreamHandler()  # 콘솔 로그
    ]
)
logger = logging.getLogger(__name__)  # 현재 모듈용 로거 생성


class LawDocumentBatchProcessor:
    """법령 문서 배치 처리 클래스"""
    
    def __init__(self, data_directory: str = "data/laws"):
        """
        배치 처리기 초기화
        
        Args:
            data_directory: 법령 데이터 디렉토리 경로
        """
        self.data_directory = Path(data_directory)  # 데이터 디렉토리 경로 객체
        self.graph_manager = None  # 그래프 관리자 초기화
        self.processor = None  # 문서 처리기 초기화
        self.supported_extensions = ['.pdf', '.docx', '.doc']  # 지원하는 파일 확장자
        
    def initialize_components(self) -> bool:
        """시스템 구성 요소 초기화"""
        try:
            logger.info("🔧 시스템 구성 요소 초기화 중...")
            
            # Neo4j 그래프 관리자 초기화
            self.graph_manager = LegalGraphManager()  # 그래프 관리자 생성
            logger.info("✅ Neo4j 그래프 관리자 초기화 완료")
            
            # 문서 처리기 초기화
            self.processor = LegalDocumentProcessor(self.graph_manager)  # 문서 처리기 생성
            logger.info("✅ 문서 처리기 초기화 완료")
            
            return True  # 성공 반환
            
        except Exception as e:  # 예외 발생 시
            logger.error(f"❌ 시스템 구성 요소 초기화 실패: {e}")  # 에러 로그
            return False  # 실패 반환
    
    def scan_documents(self) -> List[Path]:
        """지원하는 법령 문서 파일 스캔"""
        logger.info(f"📂 문서 스캔 시작: {self.data_directory}")
        
        document_files = []  # 문서 파일 리스트 초기화
        
        if not self.data_directory.exists():  # 디렉토리가 존재하지 않으면
            logger.error(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {self.data_directory}")
            return document_files  # 빈 리스트 반환
        
        # 지원하는 확장자를 가진 파일 검색
        for file_path in self.data_directory.iterdir():  # 디렉토리 내 모든 파일에 대해
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:  # 지원하는 파일이면
                # 시스템 파일 제외
                if not file_path.name.startswith('.') and not file_path.name.startswith('~'):
                    document_files.append(file_path)  # 문서 파일 리스트에 추가
                    logger.info(f"📄 발견된 문서: {file_path.name}")
        
        logger.info(f"📊 총 {len(document_files)}개의 법령 문서 발견")
        return document_files  # 문서 파일 리스트 반환
    
    def clear_existing_data(self) -> bool:
        """기존 데이터 삭제 (선택사항)"""
        try:
            logger.info("🗑️ 기존 그래프 데이터 삭제 중...")
            
            # 모든 노드와 관계 삭제
            delete_query = "MATCH (n) DETACH DELETE n"  # 모든 노드 삭제 쿼리
            self.graph_manager.execute_query(delete_query)  # 쿼리 실행
            
            logger.info("✅ 기존 데이터 삭제 완료")
            return True  # 성공 반환
            
        except Exception as e:  # 예외 발생 시
            logger.error(f"❌ 기존 데이터 삭제 실패: {e}")  # 에러 로그
            return False  # 실패 반환
    
    def process_document_file(self, file_path: Path) -> Dict[str, Any]:
        """개별 문서 파일 처리"""
        logger.info(f"📖 문서 처리 시작: {file_path.name}")
        
        start_time = datetime.now()  # 처리 시작 시간
        
        try:
            # 파일 크기 확인
            file_size = file_path.stat().st_size  # 파일 크기 가져오기
            logger.info(f"📏 파일 크기: {file_size:,} bytes")
            
            # 문서 처리 실행
            result = self.processor.process_document(str(file_path))  # 문서 처리
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()  # 처리 시간 계산
            
            # 결과 정보 추가
            result.update({
                "file_name": file_path.name,  # 파일명
                "file_size": file_size,  # 파일 크기
                "processing_time": processing_time,  # 처리 시간
                "processed_at": datetime.now().isoformat()  # 처리 시간
            })
            
            if result.get("success", False):  # 성공한 경우
                logger.info(f"✅ 문서 처리 완료: {file_path.name} ({processing_time:.2f}초)")
                logger.info(f"📊 처리된 조문 수: {result.get('articles_count', 0)}개")
            else:  # 실패한 경우
                logger.error(f"❌ 문서 처리 실패: {file_path.name} - {result.get('error', 'Unknown error')}")
            
            return result  # 처리 결과 반환
            
        except Exception as e:  # 예외 발생 시
            processing_time = (datetime.now() - start_time).total_seconds()  # 처리 시간 계산
            error_result = {  # 에러 결과 생성
                "success": False,
                "error": str(e),
                "file_name": file_path.name,
                "processing_time": processing_time,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.error(f"❌ 문서 처리 중 예외 발생: {file_path.name} - {e}")
            return error_result  # 에러 결과 반환
    
    def process_all_documents(self, clear_existing: bool = False) -> Dict[str, Any]:
        """모든 법령 문서 일괄 처리"""
        logger.info("🚀 법령 문서 일괄 처리 시작")
        
        start_time = datetime.now()  # 전체 처리 시작 시간
        
        # 기존 데이터 삭제 (선택사항)
        if clear_existing:  # 기존 데이터 삭제 옵션이 켜져 있으면
            if not self.clear_existing_data():  # 삭제 실패 시
                return {"success": False, "error": "Failed to clear existing data"}
        
        # 문서 파일 스캔
        document_files = self.scan_documents()  # 문서 파일 스캔
        
        if not document_files:  # 문서 파일이 없으면
            logger.warning("⚠️ 처리할 법령 문서가 없습니다.")
            return {"success": False, "error": "No documents found to process"}
        
        # 처리 결과 저장
        results = {  # 결과 딕셔너리 초기화
            "total_files": len(document_files),  # 총 파일 수
            "processed_files": [],  # 처리된 파일 리스트
            "failed_files": [],  # 실패한 파일 리스트
            "success_count": 0,  # 성공 개수
            "error_count": 0,  # 실패 개수
            "total_articles": 0,  # 총 조문 수
            "processing_start": start_time.isoformat(),  # 처리 시작 시간
        }
        
        # 각 문서 파일 처리
        for i, file_path in enumerate(document_files, 1):  # 각 문서 파일에 대해
            logger.info(f"📈 진행률: {i}/{len(document_files)} ({i/len(document_files)*100:.1f}%)")
            
            result = self.process_document_file(file_path)  # 문서 파일 처리
            
            if result.get("success", False):  # 성공한 경우
                results["processed_files"].append(result)  # 처리된 파일에 추가
                results["success_count"] += 1  # 성공 개수 증가
                results["total_articles"] += result.get("articles_count", 0)  # 총 조문 수 누적
            else:  # 실패한 경우
                results["failed_files"].append(result)  # 실패한 파일에 추가
                results["error_count"] += 1  # 실패 개수 증가
        
        # 전체 처리 시간 계산
        total_time = (datetime.now() - start_time).total_seconds()  # 총 처리 시간
        results.update({
            "processing_end": datetime.now().isoformat(),  # 처리 종료 시간
            "total_processing_time": total_time,  # 총 처리 시간
            "success": results["success_count"] > 0  # 전체 성공 여부
        })
        
        # 최종 결과 로그
        logger.info("📊 == 법령 문서 처리 완료 ==")
        logger.info(f"✅ 성공: {results['success_count']}개")
        logger.info(f"❌ 실패: {results['error_count']}개")  
        logger.info(f"📄 총 조문 수: {results['total_articles']}개")
        logger.info(f"⏱️ 총 처리 시간: {total_time:.2f}초")
        
        return results  # 최종 결과 반환
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """처리 요약 정보 조회"""
        try:
            # 그래프 통계 조회
            stats_query = """
            CALL db.labels() YIELD label
            WITH collect(label) as labels
            UNWIND labels as label
            CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
            RETURN label, value.count as count
            """
            
            # 간단한 통계 쿼리로 대체
            simple_stats = {
                "laws": self.graph_manager.execute_query("MATCH (l:Law) RETURN count(l) as count")[0]["count"],
                "articles": self.graph_manager.execute_query("MATCH (a:Article) RETURN count(a) as count")[0]["count"],
                "sections": self.graph_manager.execute_query("MATCH (s:Section) RETURN count(s) as count")[0]["count"]
            }
            
            return simple_stats  # 통계 반환
            
        except Exception as e:  # 예외 발생 시
            logger.error(f"통계 조회 실패: {e}")
            return {}  # 빈 딕셔너리 반환


def main():
    """메인 함수"""
    print("🏗️ 도시정비사업 법령 문서 일괄 처리 시스템")
    print("=" * 60)
    
    # 배치 처리기 초기화
    processor = LawDocumentBatchProcessor()  # 배치 처리기 생성
    
    # 시스템 구성 요소 초기화
    if not processor.initialize_components():  # 초기화 실패 시
        print("❌ 시스템 초기화 실패. 프로그램을 종료합니다.")
        sys.exit(1)  # 프로그램 종료
    
    # 사용자 입력: 기존 데이터 삭제 여부
    clear_data = input("\n기존 데이터를 삭제하고 새로 로드하시겠습니까? (y/N): ").lower().strip()
    clear_existing = clear_data in ['y', 'yes', '예', 'ㅇ']  # 삭제 여부 결정
    
    if clear_existing:  # 삭제를 선택한 경우
        print("⚠️ 기존 데이터를 삭제하고 새로 로드합니다.")
    else:  # 삭제하지 않는 경우
        print("ℹ️ 기존 데이터를 유지하고 새 데이터를 추가합니다.")
    
    # 문서 처리 실행
    print("\n🚀 법령 문서 처리를 시작합니다...")
    results = processor.process_all_documents(clear_existing=clear_existing)  # 문서 일괄 처리
    
    # 처리 결과 출력
    if results["success"]:  # 성공한 경우
        print(f"\n✅ 처리 완료!")
        print(f"📊 성공: {results['success_count']}개 문서")
        print(f"📄 총 {results['total_articles']}개 조문 로드됨")
        
        if results["error_count"] > 0:  # 실패한 파일이 있는 경우
            print(f"⚠️ 실패: {results['error_count']}개 문서")
            print("\n실패한 파일들:")
            for failed in results["failed_files"]:  # 실패한 파일들 출력
                print(f"  - {failed['file_name']}: {failed['error']}")
        
        # 그래프 통계 출력
        print("\n📈 그래프 데이터베이스 현황:")
        try:
            stats = processor.get_processing_summary()  # 처리 요약 조회
            for key, value in stats.items():  # 통계 항목 출력
                print(f"  - {key}: {value:,}개")
        except Exception as e:  # 통계 조회 실패 시
            print(f"  통계 조회 실패: {e}")
            
    else:  # 실패한 경우
        print(f"\n❌ 처리 실패: {results.get('error', 'Unknown error')}")
        
    print(f"\n⏱️ 총 처리 시간: {results.get('total_processing_time', 0):.2f}초")
    print("프로그램을 종료합니다.")


if __name__ == "__main__":  # 스크립트가 직접 실행될 때
    main()  # 메인 함수 호출 