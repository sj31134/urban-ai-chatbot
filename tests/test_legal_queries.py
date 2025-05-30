"""
도시정비 법령 RAG 시스템 테스트 케이스
법령 질의응답의 정확성 및 출처 검증 테스트
"""

import sys
import os
import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.graph.legal_graph import LegalGraphManager
from src.rag.legal_rag_chain import LegalRAGChain
from src.rag.document_processor import LegalDocumentProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLegalQueries:
    """법령 질의응답 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        try:
            cls.graph_manager = LegalGraphManager()
            cls.rag_chain = LegalRAGChain(cls.graph_manager)
            logger.info("테스트 환경 초기화 완료")
        except Exception as e:
            logger.error(f"테스트 환경 초기화 실패: {e}")
            pytest.skip("테스트 환경 초기화 실패")
    
    @classmethod
    def teardown_class(cls):
        """테스트 클래스 정리"""
        if hasattr(cls, 'graph_manager'):
            cls.graph_manager.close()
            logger.info("테스트 환경 정리 완료")


class TestUrbanRedevelopmentQueries(TestLegalQueries):
    """도시정비법 관련 질의 테스트"""
    
    TEST_QUERIES = [
        {
            "id": "URB_001",
            "question": "재개발 조합 설립 요건은 무엇인가요?",
            "expected_sources": ["도시정비법 제24조", "도시정비법 제25조"],
            "expected_keywords": ["조합", "설립", "동의", "토지등소유자"],
            "accuracy_threshold": 0.85,
            "category": "조합설립"
        },
        {
            "id": "URB_002", 
            "question": "정비사업 시행인가 신청 시 필요한 서류는?",
            "expected_sources": ["도시정비법 제28조", "도시정비법 시행령"],
            "expected_keywords": ["시행인가", "신청서류", "사업계획서"],
            "accuracy_threshold": 0.80,
            "category": "인허가"
        },
        {
            "id": "URB_003",
            "question": "현금청산 대상자는 누구인가요?",
            "expected_sources": ["도시정비법 제49조", "도시정비법 제50조"],
            "expected_keywords": ["현금청산", "소형주택", "부족면적"],
            "accuracy_threshold": 0.88,
            "category": "현금청산"
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)
    def test_urban_redevelopment_queries(self, test_case):
        """도시정비법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])
        
        # 기본 응답 검증
        assert result["answer"] is not None
        assert len(result["answer"]) > 50, "답변이 너무 짧습니다"
        
        # 신뢰도 검증
        assert result["confidence"] >= test_case["accuracy_threshold"], \
            f"신뢰도가 기준치({test_case['accuracy_threshold']})보다 낮습니다: {result['confidence']}"
        
        # 출처 검증
        sources = result["sources"]
        assert len(sources) > 0, "출처가 제공되지 않았습니다"
        
        # 예상 출처 포함 여부 검증
        found_sources = [source.get("source", "") for source in sources]
        expected_found = any(
            any(expected in found for found in found_sources)
            for expected in test_case["expected_sources"]
        )
        assert expected_found, f"예상 출처가 포함되지 않았습니다: {test_case['expected_sources']}"
        
        # 키워드 포함 여부 검증
        answer_lower = result["answer"].lower()
        keyword_found = any(
            keyword in answer_lower for keyword in test_case["expected_keywords"]
        )
        assert keyword_found, f"예상 키워드가 포함되지 않았습니다: {test_case['expected_keywords']}"
        
        logger.info(f"테스트 통과: {test_case['id']} - {test_case['question'][:30]}...")


class TestSmallScaleHousingQueries(TestLegalQueries):
    """소규모주택정비법 관련 질의 테스트"""
    
    TEST_QUERIES = [
        {
            "id": "SSH_001",
            "question": "소규모재개발사업에서 현금청산이 제외되는 경우는?",
            "expected_sources": ["소규모주택정비법 제17조의2"],
            "expected_keywords": ["소규모재개발", "현금청산", "제외", "예외"],
            "accuracy_threshold": 0.82,
            "category": "현금청산특례"
        },
        {
            "id": "SSH_002",
            "question": "가로주택정비사업의 대상 요건은?",
            "expected_sources": ["소규모주택정비법 제18조", "소규모주택정비법 제19조"],
            "expected_keywords": ["가로주택", "대상", "요건", "노후불량"],
            "accuracy_threshold": 0.80,
            "category": "가로주택정비"
        },
        {
            "id": "SSH_003",
            "question": "자율주택정비사업 시행자는 누구인가요?",
            "expected_sources": ["소규모주택정비법 제22조"],
            "expected_keywords": ["자율주택", "시행자", "토지등소유자"],
            "accuracy_threshold": 0.85,
            "category": "자율주택정비"
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)
    def test_small_scale_housing_queries(self, test_case):
        """소규모주택정비법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])
        
        # 기본 검증
        assert result["answer"] is not None
        assert result["confidence"] >= test_case["accuracy_threshold"]
        
        # 출처 법령 검증 (소규모주택정비법 포함 여부)
        sources = result["sources"]
        small_scale_law_found = any(
            "소규모주택정비법" in source.get("law_name", "")
            for source in sources
        )
        assert small_scale_law_found, "소규모주택정비법 출처가 포함되지 않았습니다"
        
        logger.info(f"소규모주택정비법 테스트 통과: {test_case['id']}")


class TestVacantHouseQueries(TestLegalQueries):
    """빈집정비특례법 관련 질의 테스트"""
    
    TEST_QUERIES = [
        {
            "id": "VH_001",
            "question": "빈집정비사업의 특례 내용은 무엇인가요?",
            "expected_sources": ["빈집정비특례법"],
            "expected_keywords": ["빈집", "특례", "정비사업"],
            "accuracy_threshold": 0.75,
            "category": "빈집정비특례"
        }
    ]
    
    @pytest.mark.parametrize("test_case", TEST_QUERIES)
    def test_vacant_house_queries(self, test_case):
        """빈집정비특례법 질의 테스트"""
        result = self.rag_chain.query_with_sources(test_case["question"])
        
        # 기본 검증
        assert result["answer"] is not None
        assert result["confidence"] >= test_case["accuracy_threshold"]
        
        logger.info(f"빈집정비특례법 테스트 통과: {test_case['id']}")


class TestCrossLawQueries(TestLegalQueries):
    """법령 간 교차 참조 질의 테스트"""
    
    def test_cross_reference_queries(self):
        """법령 간 교차 참조 테스트"""
        queries = [
            "도시정비법과 소규모주택정비법의 차이점은?",
            "재개발과 소규모재개발의 구분 기준은?",
            "현금청산 관련 도시정비법과 소규모주택정비법 규정 비교"
        ]
        
        for query in queries:
            result = self.rag_chain.query_with_sources(query)
            
            # 복수 법령 출처 확인
            law_names = set([
                source.get("law_name", "") 
                for source in result["sources"]
            ])
            
            # 최소 2개 이상의 서로 다른 법령이 참조되어야 함
            assert len(law_names) >= 2, f"교차 참조 쿼리에서 단일 법령만 참조됨: {law_names}"
            
            logger.info(f"교차 참조 테스트 통과: {query[:30]}... (참조 법령: {law_names})")


class TestSourceValidation(TestLegalQueries):
    """출처 검증 테스트"""
    
    def test_source_format_validation(self):
        """출처 형식 검증 테스트"""
        test_query = "재개발 조합 설립 동의 요건은?"
        result = self.rag_chain.query_with_sources(test_query)
        
        # 출처 검증 실행
        validation_result = self.rag_chain.validate_legal_sources(
            result["answer"], result["sources"]
        )
        
        # 검증 결과 확인
        assert "is_valid" in validation_result
        assert "issues" in validation_result
        assert "suggestions" in validation_result
        
        # 심각한 오류가 없어야 함
        critical_issues = [
            issue for issue in validation_result["issues"]
            if "잘못된 조문 번호" in issue
        ]
        assert len(critical_issues) == 0, f"심각한 출처 오류 발견: {critical_issues}"
        
        logger.info("출처 검증 테스트 통과")
    
    def test_article_number_format(self):
        """조문 번호 형식 테스트"""
        import re
        
        test_query = "도시정비법 제24조 내용을 알려주세요"
        result = self.rag_chain.query_with_sources(test_query)
        
        article_pattern = re.compile(r'^제\d+조(의\d+)?$')
        
        for source in result["sources"]:
            article_number = source.get("article_number", "")
            if article_number:
                assert article_pattern.match(article_number), \
                    f"잘못된 조문 번호 형식: {article_number}"
        
        logger.info("조문 번호 형식 테스트 통과")


class TestPerformance(TestLegalQueries):
    """성능 테스트"""
    
    def test_response_time(self):
        """응답 시간 테스트"""
        import time
        
        test_queries = [
            "재개발 조합 설립 요건은?",
            "소규모재개발사업 특례는?",
            "현금청산 대상자는?"
        ]
        
        response_times = []
        
        for query in test_queries:
            start_time = time.time()
            result = self.rag_chain.query_with_sources(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # 응답 시간이 30초를 초과하지 않아야 함
            assert response_time < 30, f"응답 시간 초과: {response_time:.2f}초"
            
            logger.info(f"응답 시간: {response_time:.2f}초 - {query[:30]}...")
        
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 15, f"평균 응답 시간 초과: {avg_response_time:.2f}초"
        
        logger.info(f"성능 테스트 통과 - 평균 응답 시간: {avg_response_time:.2f}초")


class TestEdgeCases(TestLegalQueries):
    """엣지 케이스 테스트"""
    
    def test_empty_query(self):
        """빈 질의 테스트"""
        result = self.rag_chain.query_with_sources("")
        
        # 빈 질의에 대한 적절한 처리 확인
        assert result["answer"] is not None
        assert result["confidence"] >= 0.0
        
        logger.info("빈 질의 테스트 통과")
    
    def test_very_long_query(self):
        """매우 긴 질의 테스트"""
        long_query = "재개발 " * 100 + "조합 설립 요건은 무엇인가요?"
        
        result = self.rag_chain.query_with_sources(long_query)
        
        # 긴 질의도 적절히 처리되어야 함
        assert result["answer"] is not None
        assert len(result["sources"]) > 0
        
        logger.info("긴 질의 테스트 통과")
    
    def test_irrelevant_query(self):
        """무관한 질의 테스트"""
        irrelevant_queries = [
            "오늘 날씨는 어떤가요?",
            "파이썬 프로그래밍 방법을 알려주세요",
            "맛있는 음식 추천해주세요"
        ]
        
        for query in irrelevant_queries:
            result = self.rag_chain.query_with_sources(query)
            
            # 무관한 질의에 대해서는 낮은 신뢰도를 가져야 함
            assert result["confidence"] < 0.5, \
                f"무관한 질의에 대해 높은 신뢰도: {result['confidence']}"
            
            logger.info(f"무관한 질의 테스트 통과: {query[:30]}...")


def generate_test_report():
    """테스트 결과 보고서 생성"""
    import json
    
    # 테스트 실행 시간 및 결과 수집
    report = {
        "test_execution_time": datetime.now().isoformat(),
        "test_categories": [
            "도시정비법 질의",
            "소규모주택정비법 질의", 
            "빈집정비특례법 질의",
            "교차 참조 질의",
            "출처 검증",
            "성능 테스트",
            "엣지 케이스"
        ],
        "total_test_cases": len(TestUrbanRedevelopmentQueries.TEST_QUERIES) + 
                           len(TestSmallScaleHousingQueries.TEST_QUERIES) + 
                           len(TestVacantHouseQueries.TEST_QUERIES),
        "performance_requirements": {
            "max_response_time": "30초",
            "avg_response_time": "15초 이하",
            "min_confidence": "법령별 차등 적용"
        }
    }
    
    # 보고서 저장
    with open("tests/test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("테스트 보고서 생성 완료: tests/test_report.json")


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v", "--tb=short"])
    
    # 보고서 생성
    generate_test_report() 