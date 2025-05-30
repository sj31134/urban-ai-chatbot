"""
도시정비 법령 문서 처리 파이프라인
PDF, DOCX 등 법령 문서를 구조화하여 Neo4j 그래프로 변환
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

import PyPDF2
import pypdf
from docx import Document
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument

from src.graph.legal_graph import LegalGraphManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalDocumentProcessor:
    """법령 문서 처리 및 그래프 변환 클래스"""
    
    def __init__(self, graph_manager: LegalGraphManager, schema_path: str = "config/legal_schema.json"):
        """
        문서 처리기 초기화
        
        Args:
            graph_manager: Neo4j 그래프 관리자
            schema_path: 법령 스키마 설정 파일 경로
        """
        self.graph_manager = graph_manager
        self.schema = self._load_schema(schema_path)
        self.text_splitter = self._create_text_splitter()
        
        # 법령 구조 패턴
        self.article_pattern = re.compile(r'제(\d+)조(의\d+)?')
        self.section_pattern = re.compile(r'제(\d+)편|제(\d+)장|제(\d+)절')
        self.subsection_pattern = re.compile(r'①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩')
        self.item_pattern = re.compile(r'\d+\.|가\.|나\.|다\.|라\.|마\.|바\.|사\.|아\.|자\.|차\.|카\.|타\.|파\.|하\.')
        
    def _load_schema(self, schema_path: str) -> Dict:
        """법령 스키마 로드"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"스키마 파일을 찾을 수 없습니다: {schema_path}")
            return {}
    
    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """법령 구조를 고려한 텍스트 분할기 생성"""
        chunk_config = self.schema.get("document_processing", {}).get("chunk_strategy", {})
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_config.get("chunk_size", 512),
            chunk_overlap=chunk_config.get("chunk_overlap", 50),
            separators=chunk_config.get("separators", ["제", "조", "항", "호", "목"]),
            keep_separator=True,
            add_start_index=True
        )
    
    def process_pdf_document(self, file_path: str, law_code: str) -> Dict:
        """PDF 법령 문서 처리"""
        logger.info(f"PDF 문서 처리 시작: {file_path}")
        
        # PDF 텍스트 추출
        text_content = self._extract_pdf_text(file_path)
        
        # 법령 정보 추출
        law_info = self._extract_law_metadata(text_content, law_code)
        
        # 조문별 분할
        articles = self._extract_articles(text_content, law_code)
        
        # Neo4j에 저장
        result = self._save_to_graph(law_info, articles)
        
        logger.info(f"PDF 처리 완료: {len(articles)}개 조문 처리")
        return result
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            with open(file_path, 'rb') as file:
                # pypdf 사용 (최신 버전)
                reader = pypdf.PdfReader(file)
                text_content = ""
                
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
                
                return text_content.strip()
                
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            # 대안으로 PyPDF2 시도
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    
                    for page in reader.pages:
                        text_content += page.extract_text() + "\n"
                    
                    return text_content.strip()
            except Exception as e2:
                logger.error(f"PDF 텍스트 추출 실패 (PyPDF2): {e2}")
                return ""
    
    def _extract_law_metadata(self, text_content: str, law_code: str) -> Dict:
        """법령 메타데이터 추출"""
        law_info = {
            "law_id": law_code,
            "category": "법률",
            "status": "시행",
            "created_at": datetime.now().isoformat()
        }
        
        # 법령명 추출
        title_patterns = [
            r'([가-힣\s]+법)\s*\n',
            r'([가-힣\s]+에\s*관한\s*법률)',
            r'([가-힣\s]+특례법)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text_content[:500])
            if match:
                law_info["name"] = match.group(1).strip()
                break
        
        # 시행일 추출
        date_patterns = [
            r'시행일\s*[:：]\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일',
            r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*시행',
            r'(\d{4})-(\d{2})-(\d{2})\s*시행'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content[:1000])
            if match:
                year, month, day = match.groups()
                law_info["effective_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break
        
        return law_info
    
    def _extract_articles(self, text_content: str, law_code: str) -> List[Dict]:
        """조문별로 텍스트 분할 및 메타데이터 추출"""
        articles = []
        
        # 조문 분할
        article_blocks = self._split_by_articles(text_content)
        
        current_section = ""
        current_chapter = ""
        
        for block in article_blocks:
            article_info = self._parse_article_block(block, law_code)
            
            if article_info:
                # 편장절 정보 업데이트
                section_match = self.section_pattern.search(block[:100])
                if section_match:
                    current_section = section_match.group(0)
                
                article_info["section"] = current_section
                article_info["chapter"] = current_chapter
                articles.append(article_info)
        
        return articles
    
    def _split_by_articles(self, text_content: str) -> List[str]:
        """조문 기준으로 텍스트 분할"""
        # 조문 시작 패턴으로 분할
        article_starts = []
        for match in self.article_pattern.finditer(text_content):
            article_starts.append(match.start())
        
        if not article_starts:
            return [text_content]
        
        # 각 조문 블록 추출
        blocks = []
        for i, start in enumerate(article_starts):
            if i < len(article_starts) - 1:
                end = article_starts[i + 1]
                blocks.append(text_content[start:end])
            else:
                blocks.append(text_content[start:])
        
        return blocks
    
    def _parse_article_block(self, block: str, law_code: str) -> Optional[Dict]:
        """개별 조문 블록 파싱"""
        # 조문 번호 추출
        article_match = self.article_pattern.search(block)
        if not article_match:
            return None
        
        article_number = article_match.group(0)
        
        # 조문 내용 정리
        content = block.strip()
        # 불필요한 공백 및 개행 정리
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', '\n', content)
        
        # 항 분할 (①, ②, ③ 등)
        subsections = self._extract_subsections(content)
        
        # 호 추출 (1., 2., 3. 또는 가., 나., 다. 등)
        items = self._extract_items(content)
        
        article_info = {
            "law_id": law_code,
            "article_number": article_number,
            "content": content,
            "subsections": subsections,
            "items": items,
            "last_updated": datetime.now().isoformat()
        }
        
        # 조문 간 참조 관계 찾기
        references = self._find_article_references(content)
        if references:
            article_info["references"] = references
        
        return article_info
    
    def _extract_subsections(self, content: str) -> List[str]:
        """항 분할 (①, ②, ③ 등)"""
        subsections = []
        subsection_matches = list(self.subsection_pattern.finditer(content))
        
        for i, match in enumerate(subsection_matches):
            start = match.start()
            if i < len(subsection_matches) - 1:
                end = subsection_matches[i + 1].start()
                subsection_text = content[start:end].strip()
            else:
                subsection_text = content[start:].strip()
            
            if subsection_text:
                subsections.append(subsection_text)
        
        return subsections
    
    def _extract_items(self, content: str) -> List[str]:
        """호 추출 (1., 2., 3. 또는 가., 나., 다. 등)"""
        items = []
        item_matches = list(self.item_pattern.finditer(content))
        
        for i, match in enumerate(item_matches):
            start = match.start()
            if i < len(item_matches) - 1:
                end = item_matches[i + 1].start()
                item_text = content[start:end].strip()
            else:
                # 다음 항이나 조문까지
                next_subsection = self.subsection_pattern.search(content, start)
                next_article = self.article_pattern.search(content, start)
                
                end = content[start:].find('\n제')
                if end == -1:
                    item_text = content[start:].strip()
                else:
                    item_text = content[start:start+end].strip()
            
            if item_text:
                items.append(item_text)
        
        return items
    
    def _find_article_references(self, content: str) -> List[str]:
        """조문 내 다른 조문 참조 찾기"""
        reference_patterns = [
            r'제(\d+)조(의\d+)?',
            r'같은\s*법\s*제(\d+)조',
            r'이\s*법\s*제(\d+)조',
            r'동법\s*제(\d+)조'
        ]
        
        references = set()
        for pattern in reference_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if '조' in pattern:
                    references.add(match.group(0))
                else:
                    references.add(f"제{match.group(1)}조")
        
        return list(references)
    
    def _save_to_graph(self, law_info: Dict, articles: List[Dict]) -> Dict:
        """Neo4j 그래프에 법령 데이터 저장"""
        try:
            # 법령 노드 생성
            law_id = self.graph_manager.create_law_node(law_info)
            
            article_nodes = []
            
            # 조문 노드 생성
            for article in articles:
                node_id = self.graph_manager.create_article_node(article)
                article_nodes.append({
                    "node_id": node_id,
                    "article_number": article["article_number"],
                    "references": article.get("references", [])
                })
                
                # 조문-법령 관계 생성
                self.graph_manager.create_relationship(
                    node_id, law_id, "BELONGS_TO",
                    {"section": article.get("section", "")}
                )
            
            # 조문 간 참조 관계 생성
            self._create_cross_references(article_nodes)
            
            result = {
                "law_id": law_id,
                "articles_count": len(articles),
                "success": True,
                "message": f"법령 '{law_info.get('name', 'Unknown')}' 처리 완료"
            }
            
            logger.info(f"그래프 저장 완료: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"그래프 저장 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "그래프 저장 중 오류 발생"
            }
    
    def _create_cross_references(self, article_nodes: List[Dict]):
        """조문 간 상호 참조 관계 생성"""
        # 조문 번호별 노드 매핑
        article_map = {
            node["article_number"]: node["node_id"] 
            for node in article_nodes
        }
        
        for node in article_nodes:
            references = node.get("references", [])
            from_node_id = node["node_id"]
            
            for ref_article in references:
                if ref_article in article_map:
                    to_node_id = article_map[ref_article]
                    
                    # 참조 관계 생성
                    self.graph_manager.create_relationship(
                        from_node_id, to_node_id, "REFERENCES",
                        {
                            "reference_type": "direct",
                            "context": "조문 참조"
                        }
                    )
    
    def process_documents_batch(self, data_directory: str) -> Dict:
        """데이터 디렉토리의 모든 법령 문서 일괄 처리"""
        logger.info(f"일괄 처리 시작: {data_directory}")
        
        results = {}
        
        # 법령 파일 처리
        laws_dir = Path(data_directory) / "laws"
        if laws_dir.exists():
            for pdf_file in laws_dir.glob("*.pdf"):
                # 파일명에서 법령 코드 추정
                law_code = self._infer_law_code(pdf_file.name)
                result = self.process_pdf_document(str(pdf_file), law_code)
                results[pdf_file.name] = result
        
        # 조례 파일 처리
        ordinances_dir = Path(data_directory) / "ordinances"
        if ordinances_dir.exists():
            for pdf_file in ordinances_dir.glob("*.pdf"):
                law_code = self._infer_law_code(pdf_file.name)
                result = self.process_pdf_document(str(pdf_file), law_code)
                results[pdf_file.name] = result
        
        logger.info(f"일괄 처리 완료: {len(results)}개 파일 처리")
        return results
    
    def _infer_law_code(self, filename: str) -> str:
        """파일명에서 법령 코드 추정"""
        code_mapping = {
            "도시정비법": "URBAN_REDEVELOPMENT_LAW",
            "소규모주택정비법": "SMALL_SCALE_HOUSING_LAW",
            "빈집정비특례법": "VACANT_HOUSE_SPECIAL_LAW",
            "서울시": "SEOUL_ORDINANCE",
            "부산시": "BUSAN_ORDINANCE"
        }
        
        for keyword, code in code_mapping.items():
            if keyword in filename:
                return code
        
        # 기본값
        return f"LAW_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# 사용 예시
if __name__ == "__main__":
    # 그래프 관리자 초기화
    graph_manager = LegalGraphManager()
    
    # 문서 처리기 초기화
    processor = LegalDocumentProcessor(graph_manager)
    
    # 샘플 문서 처리
    # result = processor.process_pdf_document("data/laws/도시정비법_전문.pdf", "URBAN_REDEVELOPMENT_LAW")
    # print(f"처리 결과: {result}")
    
    # 일괄 처리
    results = processor.process_documents_batch("data")
    print(f"일괄 처리 결과: {results}")
    
    # 연결 종료
    graph_manager.close() 