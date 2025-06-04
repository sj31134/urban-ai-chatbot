"""
향상된 RAG 파이프라인
- 임베딩 저장 및 관리
- 벡터 검색 최적화  
- 하이브리드 검색 (벡터 + 키워드)
- 컨텍스트 랭킹
"""

import os
import json
import pickle
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

# 벡터 데이터베이스
import chromadb
from chromadb.config import Settings

# 임베딩 모델
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings

# 텍스트 처리
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# 검색 및 랭킹
from rank_bm25 import BM25Okapi
import faiss

from src.graph.legal_graph import LegalGraphManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedEmbeddingManager:
    """향상된 임베딩 관리자"""
    
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask", 
                 persist_directory: str = "data/embeddings"):
        """
        임베딩 관리자 초기화
        
        Args:
            model_name: 사용할 한국어 임베딩 모델
            persist_directory: 임베딩 저장 디렉토리
        """
        self.model_name = model_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 임베딩 모델 초기화
        self.embedding_model = SentenceTransformer(model_name)
        
        # ChromaDB 초기화 (벡터 데이터베이스)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_directory / "chroma")
        )
        
        # 컬렉션 생성/가져오기
        self.collection = self.chroma_client.get_or_create_collection(
            name="legal_documents",
            metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
        )
        
        # 메타데이터 저장소
        self.metadata_file = self.persist_directory / "metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"임베딩 관리자 초기화 완료: {model_name}")
    
    def _load_metadata(self) -> Dict:
        """메타데이터 로드"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "model_name": self.model_name,
            "created_at": datetime.now().isoformat(),
            "document_count": 0,
            "chunk_count": 0
        }
    
    def _save_metadata(self):
        """메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """문서들의 임베딩 생성 및 저장"""
        logger.info(f"문서 임베딩 시작: {len(documents)}개 문서")
        
        # 텍스트 분할기
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separators=["제", "조", "항", "호", "목", "\n", ".", "!"]
        )
        
        # 배치 처리
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        for doc_idx, doc in enumerate(documents):
            # 문서 텍스트 분할
            chunks = text_splitter.split_text(doc['content'])
            
            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk.strip()) < 20:  # 너무 짧은 청크 제외
                    continue
                
                chunk_id = f"{doc['law_id']}_{doc['article_number']}_{chunk_idx}"
                
                all_chunks.append(chunk)
                all_metadatas.append({
                    'law_id': doc['law_id'],
                    'article_number': doc['article_number'],
                    'chunk_index': chunk_idx,
                    'section': doc.get('section', ''),
                    'document_type': 'article'
                })
                all_ids.append(chunk_id)
        
        # 배치로 임베딩 생성 및 저장
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i+batch_size]
            batch_metadatas = all_metadatas[i:i+batch_size]
            batch_ids = all_ids[i:i+batch_size]
            
            # 임베딩 생성
            embeddings = self.embedding_model.encode(
                batch_chunks, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            # ChromaDB에 저장
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            logger.info(f"배치 처리 완료: {i+len(batch_chunks)}/{len(all_chunks)}")
        
        # 메타데이터 업데이트
        self.metadata['document_count'] += len(documents)
        self.metadata['chunk_count'] += len(all_chunks)
        self.metadata['last_updated'] = datetime.now().isoformat()
        self._save_metadata()
        
        logger.info(f"임베딩 저장 완료: {len(all_chunks)}개 청크")
    
    def similarity_search(self, query: str, k: int = 10, 
                         filter_metadata: Dict = None) -> List[Dict]:
        """벡터 유사도 기반 검색"""
        # 쿼리 임베딩
        query_embedding = self.embedding_model.encode([query])
        
        # 필터 조건 설정
        where_filter = filter_metadata if filter_metadata else None
        
        # 검색 실행
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k,
            where=where_filter
        )
        
        # 결과 정리
        search_results = []
        for i in range(len(results['documents'][0])):
            search_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity_score': 1 - results['distances'][0][i],  # 거리를 유사도로 변환
                'id': results['ids'][0][i]
            })
        
        return search_results
    
    def get_embedding_stats(self) -> Dict:
        """임베딩 통계 정보"""
        collection_count = self.collection.count()
        
        return {
            "model_name": self.model_name,
            "total_chunks": collection_count,
            "metadata": self.metadata
        }


class HybridSearchEngine:
    """하이브리드 검색 엔진 (벡터 + 키워드)"""
    
    def __init__(self, embedding_manager: EnhancedEmbeddingManager,
                 graph_manager: LegalGraphManager):
        """
        하이브리드 검색 엔진 초기화
        
        Args:
            embedding_manager: 임베딩 관리자
            graph_manager: 그래프 관리자
        """
        self.embedding_manager = embedding_manager
        self.graph_manager = graph_manager
        
        # BM25 키워드 검색 인덱스
        self.bm25_index = None
        self.documents_corpus = []
        self.document_metadata = []
        
        self._build_bm25_index()
        
        logger.info("하이브리드 검색 엔진 초기화 완료")
    
    def _build_bm25_index(self):
        """BM25 키워드 검색 인덱스 구축"""
        logger.info("BM25 인덱스 구축 중...")
        
        # Neo4j에서 모든 조문 가져오기
        query = """
        MATCH (a:Article)-[:BELONGS_TO]->(l:Law)
        RETURN a.content as content, 
               a.article_number as article_number,
               a.law_id as law_id,
               l.name as law_name,
               a.section as section
        """
        
        results = self.graph_manager.execute_query(query)
        
        # 문서 코퍼스 구축
        for result in results:
            content = result['content']
            if content and len(content.strip()) > 10:
                # 한국어 토큰화 (간단한 공백 기반)
                tokens = content.split()
                self.documents_corpus.append(tokens)
                self.document_metadata.append({
                    'content': content,
                    'article_number': result['article_number'],
                    'law_id': result['law_id'],
                    'law_name': result['law_name'],
                    'section': result['section']
                })
        
        # BM25 인덱스 생성
        if self.documents_corpus:
            self.bm25_index = BM25Okapi(self.documents_corpus)
            logger.info(f"BM25 인덱스 구축 완료: {len(self.documents_corpus)}개 문서")
    
    def keyword_search(self, query: str, k: int = 10) -> List[Dict]:
        """키워드 기반 검색 (BM25)"""
        if not self.bm25_index:
            return []
        
        # 쿼리 토큰화
        query_tokens = query.split()
        
        # BM25 점수 계산
        scores = self.bm25_index.get_scores(query_tokens)
        
        # 상위 k개 결과 추출
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 점수가 0보다 큰 것만
                results.append({
                    'content': self.document_metadata[idx]['content'],
                    'metadata': self.document_metadata[idx],
                    'bm25_score': float(scores[idx]),
                    'search_type': 'keyword'
                })
        
        return results
    
    def hybrid_search(self, query: str, k: int = 10, 
                     vector_weight: float = 0.7, 
                     keyword_weight: float = 0.3) -> List[Dict]:
        """하이브리드 검색 (벡터 + 키워드)"""
        logger.info(f"하이브리드 검색 실행: '{query}'")
        
        # 벡터 검색
        vector_results = self.embedding_manager.similarity_search(query, k=k*2)
        
        # 키워드 검색
        keyword_results = self.keyword_search(query, k=k*2)
        
        # 결과 통합 및 점수 조합
        combined_results = {}
        
        # 벡터 검색 결과 처리
        for result in vector_results:
            key = result['metadata']['law_id'] + '_' + result['metadata']['article_number']
            combined_results[key] = {
                'content': result['content'],
                'metadata': result['metadata'],
                'vector_score': result['similarity_score'],
                'keyword_score': 0.0,
                'search_type': 'hybrid'
            }
        
        # 키워드 검색 결과 처리
        for result in keyword_results:
            key = result['metadata']['law_id'] + '_' + result['metadata']['article_number']
            if key in combined_results:
                combined_results[key]['keyword_score'] = result['bm25_score']
            else:
                combined_results[key] = {
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'vector_score': 0.0,
                    'keyword_score': result['bm25_score'],
                    'search_type': 'hybrid'
                }
        
        # 점수 정규화 및 조합
        final_results = []
        
        # 정규화를 위한 최대값 계산
        max_vector_score = max([r['vector_score'] for r in combined_results.values()]) or 1.0
        max_keyword_score = max([r['keyword_score'] for r in combined_results.values()]) or 1.0
        
        for result in combined_results.values():
            # 정규화된 점수
            norm_vector_score = result['vector_score'] / max_vector_score
            norm_keyword_score = result['keyword_score'] / max_keyword_score
            
            # 가중 평균
            combined_score = (vector_weight * norm_vector_score + 
                            keyword_weight * norm_keyword_score)
            
            result['combined_score'] = combined_score
            final_results.append(result)
        
        # 점수순 정렬
        final_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        logger.info(f"하이브리드 검색 완료: {len(final_results[:k])}개 결과")
        return final_results[:k]


class EnhancedRAGPipeline:
    """향상된 RAG 파이프라인"""
    
    def __init__(self, graph_manager: LegalGraphManager):
        """RAG 파이프라인 초기화"""
        self.graph_manager = graph_manager
        
        # 임베딩 관리자 초기화
        self.embedding_manager = EnhancedEmbeddingManager()
        
        # 하이브리드 검색 엔진 초기화
        self.search_engine = HybridSearchEngine(
            self.embedding_manager, 
            self.graph_manager
        )
        
        logger.info("향상된 RAG 파이프라인 초기화 완료")
    
    def index_all_documents(self):
        """모든 문서 인덱싱"""
        logger.info("전체 문서 인덱싱 시작...")
        
        # Neo4j에서 모든 조문 가져오기
        query = """
        MATCH (a:Article)-[:BELONGS_TO]->(l:Law)
        RETURN a.content as content,
               a.article_number as article_number, 
               a.law_id as law_id,
               a.section as section,
               l.name as law_name
        """
        
        results = self.graph_manager.execute_query(query)
        
        # 문서 형태로 변환
        documents = []
        for result in results:
            if result['content'] and len(result['content'].strip()) > 20:
                documents.append({
                    'content': result['content'],
                    'article_number': result['article_number'],
                    'law_id': result['law_id'],
                    'section': result['section'] or '',
                    'law_name': result['law_name']
                })
        
        # 임베딩 생성 및 저장
        if documents:
            self.embedding_manager.add_documents(documents)
            logger.info(f"문서 인덱싱 완료: {len(documents)}개 문서")
        else:
            logger.warning("인덱싱할 문서가 없습니다.")
    
    def search(self, query: str, search_type: str = "hybrid", k: int = 5) -> List[Dict]:
        """
        통합 검색 인터페이스
        
        Args:
            query: 검색 쿼리
            search_type: 검색 타입 ('vector', 'keyword', 'hybrid')
            k: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        if search_type == "vector":
            return self.embedding_manager.similarity_search(query, k=k)
        elif search_type == "keyword":
            return self.search_engine.keyword_search(query, k=k)
        elif search_type == "hybrid":
            return self.search_engine.hybrid_search(query, k=k)
        else:
            raise ValueError(f"지원하지 않는 검색 타입: {search_type}")
    
    def get_system_stats(self) -> Dict:
        """시스템 통계 정보"""
        embedding_stats = self.embedding_manager.get_embedding_stats()
        
        # 그래프 통계
        graph_stats = self.graph_manager.execute_query(
            "MATCH (n) RETURN labels(n) as label, count(n) as count"
        )
        
        return {
            "embedding_stats": embedding_stats,
            "graph_stats": {stat['label'][0]: stat['count'] for stat in graph_stats},
            "search_engine": "하이브리드 (벡터 + 키워드) 검색"
        }


# 사용 예시
if __name__ == "__main__":
    # 그래프 관리자 초기화
    graph_manager = LegalGraphManager()
    
    # RAG 파이프라인 초기화
    rag_pipeline = EnhancedRAGPipeline(graph_manager)
    
    # 모든 문서 인덱싱
    rag_pipeline.index_all_documents()
    
    # 검색 테스트
    query = "도시정비사업의 시행자"
    results = rag_pipeline.search(query, search_type="hybrid", k=5)
    
    print(f"검색 쿼리: {query}")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata']['article_number']} (점수: {result.get('combined_score', 0):.3f})")
        print(f"   {result['content'][:100]}...")
    
    # 시스템 통계
    stats = rag_pipeline.get_system_stats()
    print(f"\n시스템 통계: {stats}")
    
    # 연결 종료
    graph_manager.close() 