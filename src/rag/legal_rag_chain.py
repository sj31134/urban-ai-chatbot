"""
도시정비사업 법령 전문 RAG 체인
Neo4j 그래프와 Google Gemini를 활용한 질의응답 시스템
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseRetriever, Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.graph.legal_graph import LegalGraphManager
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalGraphRetriever:
    """Neo4j 그래프 기반 법령 검색기 (BaseRetriever 없이 자체 구현)"""
    
    def __init__(self, graph_manager: LegalGraphManager, 
                 embedding_model: Optional[str] = None,
                 similarity_threshold: float = 0.7,
                 max_results: int = 10):
        """
        그래프 검색기 초기화
        
        Args:
            graph_manager: Neo4j 그래프 관리자
            embedding_model: 임베딩 모델명
            similarity_threshold: 유사도 임계값
            max_results: 최대 검색 결과 수
        """
        self.graph_manager = graph_manager
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        
        # 임베딩 모델 초기화
        model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        # bge-m3가 아닌 안정적인 모델 사용
        if "bge-m3" in model_name:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            
        self.embedder = SentenceTransformer(model_name)
        
    def get_relevant_documents(self, query: str) -> List[Document]:
        """질의와 관련된 법령 문서 검색"""
        
        # 1. 키워드 기반 직접 검색
        keyword_results = self._keyword_search(query)
        
        # 2. 그래프 관계 기반 확장 검색
        graph_results = self._graph_expansion_search(query, keyword_results)
        
        # 3. 임베딩 기반 유사도 검색
        semantic_results = self._semantic_search(query, keyword_results + graph_results)
        
        # 4. 결과 통합 및 랭킹
        final_results = self._merge_and_rank_results(query, keyword_results, graph_results, semantic_results)
        
        return final_results[:self.max_results]
    
    def _keyword_search(self, query: str) -> List[Document]:
        """키워드 기반 조문 검색"""
        # 핵심 키워드 추출
        keywords = self._extract_keywords(query)
        
        documents = []
        for keyword in keywords:
            articles = self.graph_manager.search_articles_by_content(keyword, limit=5)
            
            for article in articles:
                doc = Document(
                    page_content=article["content"],
                    metadata={
                        "article_number": article["article_number"],
                        "law_name": article["law_name"],
                        "section": article.get("section", ""),
                        "search_type": "keyword",
                        "keyword": keyword,
                        "source": f"{article['law_name']} {article['article_number']}"
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _graph_expansion_search(self, query: str, base_results: List[Document]) -> List[Document]:
        """그래프 관계를 활용한 확장 검색"""
        expanded_docs = []
        
        for doc in base_results:
            article_number = doc.metadata.get("article_number")
            if article_number:
                # 해당 조문의 ID 찾기
                article_info = self._get_article_node_id(article_number)
                if article_info:
                    # 관련 조문들 검색 (2-hop)
                    related_articles = self.graph_manager.get_related_articles(
                        article_info["node_id"], depth=2
                    )
                    
                    for related in related_articles:
                        expanded_doc = Document(
                            page_content=related["content"],
                            metadata={
                                "article_number": related["article_number"],
                                "section": related.get("section", ""),
                                "search_type": "graph_expansion",
                                "related_to": article_number,
                                "source": f"관련조문 {related['article_number']}"
                            }
                        )
                        expanded_docs.append(expanded_doc)
        
        return expanded_docs
    
    def _semantic_search(self, query: str, candidate_docs: List[Document]) -> List[Document]:
        """임베딩 기반 의미론적 검색"""
        if not candidate_docs:
            return []
        
        # 질의 임베딩
        query_embedding = self.embedder.encode([query])
        
        # 문서 임베딩 및 유사도 계산
        doc_contents = [doc.page_content for doc in candidate_docs]
        doc_embeddings = self.embedder.encode(doc_contents)
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # 유사도 임계값 이상인 문서만 선택
        semantic_docs = []
        for i, similarity in enumerate(similarities):
            if similarity >= self.similarity_threshold:
                doc = candidate_docs[i]
                doc.metadata["similarity_score"] = float(similarity)
                doc.metadata["search_type"] = "semantic"
                semantic_docs.append(doc)
        
        # 유사도 순으로 정렬
        semantic_docs.sort(key=lambda x: x.metadata["similarity_score"], reverse=True)
        
        return semantic_docs
    
    def _merge_and_rank_results(self, query: str, keyword_results: List[Document], 
                               graph_results: List[Document], semantic_results: List[Document]) -> List[Document]:
        """검색 결과 통합 및 랭킹"""
        
        # 중복 제거를 위한 딕셔너리
        unique_docs = {}
        
        # 가중치 설정
        weights = {
            "keyword": 1.0,
            "graph_expansion": 0.8,
            "semantic": 0.9
        }
        
        all_results = keyword_results + graph_results + semantic_results
        
        for doc in all_results:
            article_number = doc.metadata.get("article_number", "")
            search_type = doc.metadata.get("search_type", "keyword")
            
            if article_number:
                # 이미 존재하는 조문인 경우 점수 누적
                if article_number in unique_docs:
                    existing_doc = unique_docs[article_number]
                    existing_score = existing_doc.metadata.get("final_score", 0)
                    new_score = weights.get(search_type, 0.5)
                    existing_doc.metadata["final_score"] = existing_score + new_score
                    
                    # 검색 타입 추가
                    search_types = existing_doc.metadata.get("search_types", [])
                    search_types.append(search_type)
                    existing_doc.metadata["search_types"] = search_types
                else:
                    # 새로운 조문
                    doc.metadata["final_score"] = weights.get(search_type, 0.5)
                    doc.metadata["search_types"] = [search_type]
                    unique_docs[article_number] = doc
        
        # 최종 점수로 정렬
        ranked_docs = list(unique_docs.values())
        ranked_docs.sort(key=lambda x: x.metadata.get("final_score", 0), reverse=True)
        
        return ranked_docs
    
    def _extract_keywords(self, query: str) -> List[str]:
        """질의에서 핵심 키워드 추출"""
        # 법령 관련 핵심 키워드
        legal_keywords = [
            "재개발", "재건축", "정비사업", "조합", "현금청산", "소규모", 
            "가로주택", "빈집", "특례", "허가", "인가", "분담금", "사업시행자"
        ]
        
        keywords = []
        query_lower = query.lower()
        
        # 법령 키워드 매칭
        for keyword in legal_keywords:
            if keyword in query:
                keywords.append(keyword)
        
        # 추가 키워드 추출 (명사 위주)
        import re
        # 한글 명사 패턴 (2글자 이상)
        noun_pattern = r'[가-힣]{2,}'
        found_nouns = re.findall(noun_pattern, query)
        
        # 중복 제거 및 기존 키워드와 합치기
        for noun in found_nouns:
            if noun not in keywords and len(noun) >= 2:
                keywords.append(noun)
        
        return keywords[:5]  # 최대 5개 키워드
    
    def _get_article_node_id(self, article_number: str) -> Optional[Dict]:
        """조문 번호로 노드 ID 조회"""
        with self.graph_manager.driver.session() as session:
            query = """
            MATCH (a:Article {article_number: $article_number})
            RETURN id(a) as node_id, a.article_number as article_number
            LIMIT 1
            """
            result = session.run(query, {"article_number": article_number})
            record = result.single()
            return dict(record) if record else None


class LegalRAGChain:
    """법령 Graph RAG 체인"""
    
    def __init__(self, graph_manager: LegalGraphManager):
        """
        법령 RAG 체인 초기화
        
        Args:
            graph_manager: Neo4j 그래프 관리자 인스턴스
        """
        # 환경변수 로드
        load_dotenv()
        
        # LLM 초기화 (Google Gemini)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.1
        )
        
        # 검색기 초기화 (자체 구현)
        self.retriever = LegalGraphRetriever(graph_manager)
        
        # 프롬프트 템플릿 설정
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> PromptTemplate:
        """법령 전문 프롬프트 템플릿 생성"""
        template = """당신은 도시정비사업 법령 전문가입니다. 
주어진 법령 조문들을 바탕으로 정확하고 신뢰할 수 있는 답변을 제공해주세요.

관련 법령 조문:
{context}

질문: {question}

답변 지침:
1. 반드시 제공된 법령 조문에 근거하여 답변하세요
2. 조문 번호와 법령명을 명시하여 출처를 분명히 하세요
3. 법령 해석은 보수적으로 접근하고, 불확실한 부분은 명시하세요
4. 실무적 조언보다는 법령 내용 자체에 집중하세요
5. 관련 조문들 간의 연관성도 설명해주세요

답변:"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def query_with_sources(self, question: str) -> Dict[str, Any]:
        """출처 포함 법령 검색 및 답변 생성"""
        try:
            # 1. 관련 문서 검색
            source_documents = self.retriever.get_relevant_documents(question)
            
            # 2. 컨텍스트 생성
            context = "\\n\\n".join([
                f"[{doc.metadata.get('law_name', '법령명 미상')} {doc.metadata.get('article_number', 'N/A')}]\\n{doc.page_content}"
                for doc in source_documents
            ])
            
            # 3. LLM으로 답변 생성
            prompt = self.prompt_template.format(context=context, question=question)
            
            # 문자열로 LLM 호출
            answer = self.llm.invoke(prompt).content
            
            # 4. 출처 정리
            sources = self._format_sources(source_documents)
            
            # 5. 신뢰도 계산
            confidence = self._calculate_confidence(source_documents, answer)
            
            # 6. 관련 조문 추천
            related_articles = self._get_related_recommendations(source_documents)
            
            response = {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "related_articles": related_articles,
                "search_metadata": {
                    "documents_found": len(source_documents),
                    "query_timestamp": datetime.now().isoformat(),
                    "search_types": list(set([
                        doc.metadata.get("search_type", "unknown") 
                        for doc in source_documents
                    ]))
                }
            }
            
            logger.info(f"질의 처리 완료: {question[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"RAG 체인 실행 오류: {e}")
            return {
                "answer": "죄송합니다. 현재 법령 검색 서비스에 문제가 발생했습니다.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _format_sources(self, source_documents: List[Document]) -> List[Dict]:
        """출처 정보 포맷팅"""
        sources = []
        
        for doc in source_documents:
            source_info = {
                "article_number": doc.metadata.get("article_number", ""),
                "law_name": doc.metadata.get("law_name", ""),
                "section": doc.metadata.get("section", ""),
                "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                "similarity_score": doc.metadata.get("similarity_score", 0.0),
                "search_type": doc.metadata.get("search_type", "keyword")
            }
            sources.append(source_info)
        
        return sources
    
    def _calculate_confidence(self, source_documents: List[Document], answer: str) -> float:
        """답변 신뢰도 계산"""
        if not source_documents:
            return 0.0
        
        # 기본 점수
        base_score = 0.7
        
        # 출처 문서 수에 따른 가중치
        doc_count_weight = min(len(source_documents) * 0.1, 0.2)
        
        # 유사도 점수 평균
        similarity_scores = [
            doc.metadata.get("similarity_score", 0.0) 
            for doc in source_documents
        ]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        similarity_weight = avg_similarity * 0.3
        
        # 검색 타입 다양성 (키워드, 그래프, 시맨틱 검색 조합)
        search_types = set([
            doc.metadata.get("search_type", "") 
            for doc in source_documents
        ])
        diversity_weight = len(search_types) * 0.05
        
        confidence = min(base_score + doc_count_weight + similarity_weight + diversity_weight, 1.0)
        return round(confidence, 2)
    
    def _get_related_recommendations(self, source_documents: List[Document]) -> List[Dict]:
        """관련 조문 추천"""
        recommendations = []
        
        # 출처 문서에서 참조되는 다른 조문들 찾기
        for doc in source_documents[:3]:  # 상위 3개 문서만
            article_number = doc.metadata.get("article_number")
            if article_number:
                # 교차 참조 찾기
                cross_refs = self.graph_manager.find_cross_references(doc.page_content)
                
                for ref in cross_refs[:2]:  # 최대 2개까지
                    recommendation = {
                        "article_number": ref["article_number"],
                        "content_preview": ref["content"][:80] + "...",
                        "relation_type": "참조관계"
                    }
                    recommendations.append(recommendation)
        
        return recommendations[:5]  # 최대 5개 추천
    
    def validate_legal_sources(self, answer: str, sources: List[Dict]) -> Dict:
        """법령 출처 정확성 검증"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # 조문 번호 형식 검증
        article_pattern = re.compile(r'^제\d+조(의\d+)?$')
        
        for source in sources:
            article_number = source.get("article_number", "")
            
            # 조문 번호 형식 확인
            if article_number and not article_pattern.match(article_number):
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"잘못된 조문 번호 형식: {article_number}")
            
            # 법령명 확인
            law_name = source.get("law_name", "")
            if not law_name:
                validation_result["issues"].append("법령명이 누락되었습니다")
        
        # 출처 다양성 확인
        if len(sources) < 2:
            validation_result["suggestions"].append("더 많은 관련 조문을 참조하는 것이 좋겠습니다")
        
        return validation_result


# 사용 예시
if __name__ == "__main__":
    # 그래프 관리자 초기화
    graph_manager = LegalGraphManager()
    
    # RAG 체인 초기화
    rag_chain = LegalRAGChain(graph_manager)
    
    # 테스트 질의
    test_questions = [
        "재개발 조합 설립 요건은 무엇인가요?",
        "소규모재개발사업에서 현금청산이 제외되는 경우는?",
        "정비사업 시행인가 절차는 어떻게 되나요?"
    ]
    
    for question in test_questions:
        print(f"\n질문: {question}")
        result = rag_chain.query_with_sources(question)
        print(f"답변: {result['answer']}")
        print(f"신뢰도: {result['confidence']}")
        print(f"출처 수: {len(result['sources'])}")
    
    # 연결 종료
    graph_manager.close() 