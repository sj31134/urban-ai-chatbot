"""
도시정비 법령 RAG 시스템 테스트 케이스
법령 질의응답의 정확성 및 출처 검증 테스트
"""

# 필요한 라이브러리 import
import sys  # 시스템 관련 기능
import os  # 운영체제 관련 기능
import pytest  # 테스트 프레임워크
import logging  # 로그 기록
from typing import Dict, List, Any  # 타입 힌트
from datetime import datetime  # 날짜/시간 처리

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(__file__))  # 상위 2단계 디렉토리 경로
sys.path.insert(0, project_root)  # 시스템 경로에 추가

# 프로젝트 내부 모듈 import
from src.graph.legal_graph import LegalGraphManager  # Neo4j 그래프 관리자
from src.rag.legal_rag_chain import LegalRAGChain  # RAG 체인 클래스
from src.rag.document_processor import LegalDocumentProcessor  # 문서 처리기

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # INFO 레벨 로깅 설정
logger = logging.getLogger(__name__)  # 현재 모듈용 로거 생성


class TestLegalQueries:
    """법령 질의응답 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        try:
            cls.graph_manager = LegalGraphManager()  # Neo4j 그래프 관리자 생성
            cls.rag_chain = LegalRAGChain(cls.graph_manager)  # RAG 체인 생성
            logger.info("테스트 환경 초기화 완료")  # 초기화 완료 로그
        except Exception as e:  # 초기화 실패 시
            logger.error(f"테스트 환경 초기화 실패: {e}")  # 에러 로그
            pytest.skip("테스트 환경 초기화 실패")  # 테스트 건너뛰기
    
    @classmethod
    def teardown_class(cls):
        """테스트 클래스 정리"""
        if hasattr(cls, 'graph_manager'):  # 그래프 관리자가 있으면
            cls.graph_manager.close()  # 연결 종료
            logger.info("테스트 환경 정리 완료")  # 정리 완료 로그


class TestUrbanRedevelopmentQueries(TestLegalQueries):
    """도시정비법 관련 질의 테스트"""
    
    TEST_QUERIES = [  # 테스트 질의 목록
        {
            "id": "URB_001",  # 테스트 ID
            "question": "재개발 조합 설립 요건은 무엇인가요?",  # 테스트 질문
            "expected_sources": ["도시정비법 제24조", "도시정비법 제25조"],  # 예상 출처
            "expected_keywords": ["조합", "설립", "동의", "토지등소유자"],  # 예상 키워드
            "accuracy_threshold": 0.85,  # 정확도 임계값
            "category": "조합설립"  # 테스트 카테고리
        },
        {
            "id": "URB_002",  # 테스트 ID
            "question": "정비사업 시행인가 신청 시 필요한 서류는?",  # 테스트 질문
            "expected_sources": ["도시정비법 제28조", "도시정비법 시행령"],  # 예상 출처
            "expected_keywords": ["시행인가", "신청서류", "사업계획서"],  # 예상 키워드
            "accuracy_threshold": 0.80,  # 정확도 임계값
            "category": "인허가"  # 테스트 카테고리
        },
        {
            "id": "URB_003",  # 테스트 ID
            "question": "현금청산 대상자는 누구인가요?",  # 테스트 질문
            "expected_sources": ["도시정비법 제49조", "도시정비법 제50조"],  # 예상 출처
            "expected_keywords": ["현금청산", "소형주택", "부족면적"],  # 예상 키워드
            "accuracy_threshold": 0.88,  # 정확도 임계값
            "category": "현금청산"  # 테스트 카테고리
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)  # 매개변수화된 테스트
    def test_urban_redevelopment_queries(self, test_case):
        """도시정비법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])  # RAG 체인으로 질의 처리
        
        # 기본 응답 검증
        assert result["answer"] is not None  # 답변이 존재하는지 확인
        assert len(result["answer"]) > 50, "답변이 너무 짧습니다"  # 답변 길이 검증
        
        # 신뢰도 검증
        assert result["confidence"] >= test_case["accuracy_threshold"], \
            f"신뢰도가 기준치({test_case['accuracy_threshold']})보다 낮습니다: {result['confidence']}"  # 신뢰도 임계값 검증
        
        # 출처 검증
        sources = result["sources"]  # 출처 정보 가져오기
        assert len(sources) > 0, "출처가 제공되지 않았습니다"  # 출처 존재 여부 확인
        
        # 예상 출처 포함 여부 검증
        found_sources = [source.get("source", "") for source in sources]  # 실제 출처 목록
        expected_found = any(  # 예상 출처 중 하나라도 포함되었는지 확인
            any(expected in found for found in found_sources)  # 각 예상 출처가 실제 출처에 포함되는지
            for expected in test_case["expected_sources"]  # 모든 예상 출처에 대해
        )
        assert expected_found, f"예상 출처가 포함되지 않았습니다: {test_case['expected_sources']}"  # 예상 출처 포함 검증
        
        # 키워드 포함 여부 검증
        answer_lower = result["answer"].lower()  # 답변을 소문자로 변환
        keyword_found = any(  # 예상 키워드 중 하나라도 포함되었는지 확인
            keyword in answer_lower for keyword in test_case["expected_keywords"]  # 각 키워드가 답변에 포함되는지
        )
        assert keyword_found, f"예상 키워드가 포함되지 않았습니다: {test_case['expected_keywords']}"  # 키워드 포함 검증
        
        logger.info(f"테스트 통과: {test_case['id']} - {test_case['question'][:30]}...")  # 테스트 통과 로그


class TestSmallScaleHousingQueries(TestLegalQueries):
    """소규모주택정비법 관련 질의 테스트"""
    
    TEST_QUERIES = [  # 테스트 질의 목록
        {
            "id": "SSH_001",  # 테스트 ID
            "question": "소규모재개발사업에서 현금청산이 제외되는 경우는?",  # 테스트 질문
            "expected_sources": ["소규모주택정비법 제17조의2"],  # 예상 출처
            "expected_keywords": ["소규모재개발", "현금청산", "제외", "예외"],  # 예상 키워드
            "accuracy_threshold": 0.82,  # 정확도 임계값
            "category": "현금청산특례"  # 테스트 카테고리
        },
        {
            "id": "SSH_002",  # 테스트 ID
            "question": "가로주택정비사업의 대상 요건은?",  # 테스트 질문
            "expected_sources": ["소규모주택정비법 제18조", "소규모주택정비법 제19조"],  # 예상 출처
            "expected_keywords": ["가로주택", "대상", "요건", "노후불량"],  # 예상 키워드
            "accuracy_threshold": 0.80,  # 정확도 임계값
            "category": "가로주택정비"  # 테스트 카테고리
        },
        {
            "id": "SSH_003",  # 테스트 ID
            "question": "자율주택정비사업 시행자는 누구인가요?",  # 테스트 질문
            "expected_sources": ["소규모주택정비법 제22조"],  # 예상 출처
            "expected_keywords": ["자율주택", "시행자", "토지등소유자"],  # 예상 키워드
            "accuracy_threshold": 0.85,  # 정확도 임계값
            "category": "자율주택정비"  # 테스트 카테고리
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)  # 매개변수화된 테스트
    def test_small_scale_housing_queries(self, test_case):
        """소규모주택정비법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])  # RAG 체인으로 질의 처리
        
        # 기본 검증
        assert result["answer"] is not None  # 답변이 존재하는지 확인
        assert result["confidence"] >= test_case["accuracy_threshold"]  # 신뢰도 임계값 검증
        
        # 출처 법령 검증 (소규모주택정비법 포함 여부)
        sources = result["sources"]  # 출처 정보 가져오기
        small_scale_law_found = any(  # 소규모주택정비법 출처가 포함되었는지 확인
            "소규모주택정비법" in source.get("law_name", "")  # 각 출처의 법령명에서 소규모주택정비법 검색
            for source in sources  # 모든 출처에 대해
        )
        assert small_scale_law_found, "소규모주택정비법 출처가 포함되지 않았습니다"  # 소규모주택정비법 출처 포함 검증
        
        logger.info(f"소규모주택정비법 테스트 통과: {test_case['id']}")  # 테스트 통과 로그


class TestVacantHouseQueries(TestLegalQueries):
    """빈집정비특례법 관련 질의 테스트"""
    
    TEST_QUERIES = [  # 테스트 질의 목록
        {
            "id": "VH_001",  # 테스트 ID
            "question": "빈집정비사업의 특례 내용은 무엇인가요?",  # 테스트 질문
            "expected_sources": ["빈집정비특례법"],  # 예상 출처
            "expected_keywords": ["빈집", "특례", "정비사업"],  # 예상 키워드
            "accuracy_threshold": 0.75,  # 정확도 임계값
            "category": "빈집정비특례"  # 테스트 카테고리
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)  # 매개변수화된 테스트
    def test_vacant_house_queries(self, test_case):
        """빈집정비특례법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])  # RAG 체인으로 질의 처리
        
        # 기본 검증
        assert result["answer"] is not None  # 답변이 존재하는지 확인
        assert result["confidence"] >= test_case["accuracy_threshold"]  # 신뢰도 임계값 검증
        
        logger.info(f"빈집정비특례법 테스트 통과: {test_case['id']}")  # 테스트 통과 로그


class TestCrossLawQueries(TestLegalQueries):
    """법령 간 교차 참조 질의 테스트"""
    
    def test_cross_reference_queries(self):
        """법령 간 교차 참조 테스트"""
        queries = [  # 교차 참조 테스트 질의 목록
            "도시정비법과 소규모주택정비법의 차이점은?",  # 법령 간 차이점 질의
            "재개발과 소규모재개발의 구분 기준은?",  # 사업 구분 기준 질의
            "현금청산 관련 도시정비법과 소규모주택정비법 규정 비교"  # 규정 비교 질의
        ]
        
        for query in queries:  # 각 질의에 대해
            result = self.rag_chain.query_with_sources(query)  # RAG 체인으로 질의 처리
            
            # 기본 검증
            assert result["answer"] is not None  # 답변이 존재하는지 확인
            assert result["confidence"] >= 0.7  # 최소 신뢰도 검증
            
            # 출처 다양성 검증 (최소 2개 이상의 서로 다른 법령)
            sources = result["sources"]  # 출처 정보 가져오기
            law_names = set(source.get("law_name", "") for source in sources)  # 고유한 법령명 집합
            assert len(law_names) >= 2, f"교차 참조 질의에 대해 다양한 법령 출처가 필요합니다: {law_names}"  # 출처 다양성 검증
            
            logger.info(f"교차 참조 테스트 통과: {query[:30]}...")  # 테스트 통과 로그


class TestSourceValidation(TestLegalQueries):
    """출처 검증 테스트"""
    
    def test_source_format_validation(self):
        """출처 형식 검증 테스트"""
        test_query = "재개발 조합 설립 동의 요건은?"  # 테스트 질의
        result = self.rag_chain.query_with_sources(test_query)  # RAG 체인으로 질의 처리
        
        sources = result["sources"]  # 출처 정보 가져오기
        assert len(sources) > 0, "출처가 제공되지 않았습니다"  # 출처 존재 여부 확인
        
        for source in sources:  # 각 출처에 대해
            # 필수 필드 검증
            assert "law_name" in source, "법령명이 누락되었습니다"  # 법령명 필드 존재 확인
            assert "article_number" in source, "조문 번호가 누락되었습니다"  # 조문번호 필드 존재 확인
            assert "content_preview" in source, "내용 미리보기가 누락되었습니다"  # 내용 미리보기 필드 존재 확인
            assert "similarity_score" in source, "유사도 점수가 누락되었습니다"  # 유사도 점수 필드 존재 확인
            
            # 유사도 점수 범위 검증
            similarity = source["similarity_score"]  # 유사도 점수 가져오기
            assert 0.0 <= similarity <= 1.0, f"유사도 점수가 범위를 벗어났습니다: {similarity}"  # 유사도 점수 범위 검증
            
            # 내용 길이 검증
            content = source["content_preview"]  # 내용 미리보기 가져오기
            assert len(content) > 10, "내용 미리보기가 너무 짧습니다"  # 내용 길이 검증
            
        logger.info("출처 형식 검증 테스트 통과")  # 테스트 통과 로그
    
    def test_article_number_format(self):
        """조문 번호 형식 검증 테스트"""
        test_query = "정비사업 시행인가 절차는?"  # 테스트 질의
        result = self.rag_chain.query_with_sources(test_query)  # RAG 체인으로 질의 처리
        
        sources = result["sources"]  # 출처 정보 가져오기
        
        for source in sources:  # 각 출처에 대해
            article_number = source.get("article_number", "")  # 조문 번호 가져오기
            if article_number:  # 조문 번호가 있으면
                # 조문 번호 형식 검증 (제N조 또는 제N조의N 형식)
                import re  # 정규표현식 모듈
                pattern = r'제\d+조(의\d+)?'  # 조문 번호 패턴
                assert re.match(pattern, article_number), \
                    f"조문 번호 형식이 올바르지 않습니다: {article_number}"  # 조문 번호 형식 검증
                    
        logger.info("조문 번호 형식 검증 테스트 통과")  # 테스트 통과 로그


class TestPerformance(TestLegalQueries):
    """성능 테스트"""
    
    def test_response_time(self):
        """응답 시간 테스트"""
        test_queries = [  # 성능 테스트 질의 목록
            "재개발 조합 설립 요건은?",  # 간단한 질의
            "정비사업 시행인가 신청 절차와 필요 서류는 무엇이며, 관련 법령 조문은?",  # 복잡한 질의
            "현금청산"  # 짧은 질의
        ]
        
        for query in test_queries:  # 각 질의에 대해
            start_time = datetime.now()  # 시작 시간 기록
            result = self.rag_chain.query_with_sources(query)  # RAG 체인으로 질의 처리
            end_time = datetime.now()  # 종료 시간 기록
            
            response_time = (end_time - start_time).total_seconds()  # 응답 시간 계산
            
            # 응답 시간 검증 (30초 이내)
            assert response_time <= 30.0, f"응답 시간이 너무 깁니다: {response_time}초"  # 응답 시간 임계값 검증
            
            # 기본 품질 검증
            assert result["answer"] is not None  # 답변이 존재하는지 확인
            assert result["confidence"] > 0.0  # 신뢰도가 0보다 큰지 확인
            
            logger.info(f"응답 시간: {response_time:.2f}초 - {query[:20]}...")  # 응답 시간 로그
        
        logger.info("성능 테스트 통과")  # 테스트 통과 로그


class TestEdgeCases(TestLegalQueries):
    """예외 상황 테스트"""
    
    def test_empty_query(self):
        """빈 질의 테스트"""
        result = self.rag_chain.query_with_sources("")  # 빈 질의 처리
        
        # 빈 질의에 대한 적절한 처리 확인
        assert result["answer"] is not None  # 답변이 존재하는지 확인
        assert result["confidence"] <= 0.5  # 낮은 신뢰도 확인
        
        logger.info("빈 질의 테스트 통과")  # 테스트 통과 로그
    
    def test_very_long_query(self):
        """매우 긴 질의 테스트"""
        long_query = "재개발 조합 설립 요건은 무엇이고 " * 50  # 매우 긴 질의 생성 (50번 반복)
        
        result = self.rag_chain.query_with_sources(long_query)  # 긴 질의 처리
        
        # 긴 질의에 대한 적절한 처리 확인
        assert result["answer"] is not None  # 답변이 존재하는지 확인
        assert len(result["sources"]) > 0  # 출처가 존재하는지 확인
        
        logger.info("긴 질의 테스트 통과")  # 테스트 통과 로그
    
    def test_irrelevant_query(self):
        """관련 없는 질의 테스트"""
        irrelevant_queries = [  # 관련 없는 질의 목록
            "오늘 날씨는 어때요?",  # 날씨 질의
            "파이썬 프로그래밍 방법을 알려주세요",  # 프로그래밍 질의
            "맛있는 음식 추천해주세요"  # 음식 추천 질의
        ]
        
        for query in irrelevant_queries:  # 각 관련 없는 질의에 대해
            result = self.rag_chain.query_with_sources(query)  # 질의 처리
            
            # 관련 없는 질의에 대한 낮은 신뢰도 확인
            assert result["confidence"] <= 0.6, \
                f"관련 없는 질의에 대해 신뢰도가 너무 높습니다: {result['confidence']}"  # 낮은 신뢰도 검증
            
            # 법령 관련 출처 부족 확인
            sources = result["sources"]  # 출처 정보 가져오기
            assert len(sources) <= 3, "관련 없는 질의에 대해 출처가 너무 많습니다"  # 출처 개수 제한 검증
            
        logger.info("관련 없는 질의 테스트 통과")  # 테스트 통과 로그


def generate_test_report():
    """테스트 보고서 생성"""
    report = {  # 테스트 보고서 딕셔너리
        "test_timestamp": datetime.now().isoformat(),  # 테스트 실행 시간
        "test_categories": [  # 테스트 카테고리 목록
            "도시정비법 질의",
            "소규모주택정비법 질의", 
            "빈집정비특례법 질의",
            "교차 참조 질의",
            "출처 검증",
            "성능 테스트",
            "예외 상황"
        ],
        "total_test_cases": 0,  # 총 테스트 케이스 수
        "passed_tests": 0,  # 통과한 테스트 수
        "failed_tests": 0,  # 실패한 테스트 수
        "performance_metrics": {  # 성능 지표
            "average_response_time": 0.0,  # 평균 응답 시간
            "average_confidence": 0.0,  # 평균 신뢰도
            "average_sources_count": 0.0  # 평균 출처 개수
        }
    }
    
    logger.info(f"테스트 보고서 생성 완료: {report}")  # 보고서 생성 로그
    return report  # 보고서 반환


if __name__ == "__main__":  # 스크립트가 직접 실행될 때
    # 테스트 실행
    pytest.main([__file__, "-v", "--tb=short"])  # pytest 실행 (상세 모드, 짧은 트레이스백)
    
    # 테스트 보고서 생성
    report = generate_test_report()  # 테스트 보고서 생성
    print(f"\n테스트 보고서: {report}")  # 보고서 출력 