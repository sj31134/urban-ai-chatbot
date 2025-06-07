"""
도시정비 법령 지식 그래프 관리 모듈
Neo4j를 활용한 법령 데이터 저장 및 검색 시스템
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalGraphSchema:
    """법령 지식 그래프 스키마 정의"""
    
    NODE_TYPES = {
        "Law": {
            "properties": ["name", "law_id", "effective_date", "last_updated", "category", "status"],
            "required": ["name", "law_id", "category"]
        },
        "Article": {
            "properties": ["article_number", "content", "section", "subsection", "last_updated"],
            "required": ["article_number", "content"]
        },
        "Ordinance": {
            "properties": ["ordinance_name", "region", "ordinance_number", "enacted_date", "last_amended"],
            "required": ["ordinance_name", "region"]
        },
        "Precedent": {
            "properties": ["case_number", "court", "decision_date", "case_type", "summary"],
            "required": ["case_number", "court", "decision_date"]
        }
    }
    
    RELATIONSHIPS = {
        "REFERENCES": {
            "description": "조문 간 참조관계",
            "properties": ["reference_type", "context"],
            "from_nodes": ["Article"],
            "to_nodes": ["Article"]
        },
        "APPLIES_TO": {
            "description": "판례-조문 적용관계", 
            "properties": ["application_type", "relevance_score"],
            "from_nodes": ["Precedent"],
            "to_nodes": ["Article"]
        },
        "IMPLEMENTS": {
            "description": "조례-법령 시행관계",
            "properties": ["implementation_date", "scope"],
            "from_nodes": ["Ordinance"],
            "to_nodes": ["Law"]
        },
        "BELONGS_TO": {
            "description": "조문이 속한 법령",
            "properties": ["chapter", "section_number"],
            "from_nodes": ["Article"],
            "to_nodes": ["Law"]
        },
        "AMENDS": {
            "description": "개정관계",
            "properties": ["amendment_date", "amendment_type"],
            "from_nodes": ["Article"],
            "to_nodes": ["Article"]
        }
    }


class LegalGraphManager:
    """법령 지식 그래프 관리 클래스"""
    
    def __init__(self, config_path: str = "config/neo4j_config.yaml"):
        """
        Neo4j 그래프 관리자 초기화
        
        Args:
            config_path: Neo4j 설정 파일 경로
        """
        load_dotenv()
        self.config = self._load_config(config_path)
        self.driver = None
        self.schema = LegalGraphSchema()
        self._connect()
        
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config_content = file.read()
                # 환경변수 치환
                import re
                for env_var in re.findall(r'\$\{([^}]+)\}', config_content):
                    env_value = os.getenv(env_var, "")
                    config_content = config_content.replace(f"${{{env_var}}}", env_value)
                
                return yaml.safe_load(config_content)
        except FileNotFoundError:
            logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}. 환경변수 사용")
            return self._get_env_config()
    
    def _get_env_config(self) -> Dict:
        """환경변수에서 설정 로드"""
        return {
            "connection": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j")
            }
        }
    
    def _connect(self):
        """Neo4j 데이터베이스 연결"""
        try:
            conn_config = self.config["connection"]
            self.driver = GraphDatabase.driver(
                conn_config["uri"],
                auth=(conn_config["username"], conn_config["password"])
            )
            # 연결 테스트
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j 데이터베이스 연결 성공")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j 데이터베이스 연결 실패: {e}")
            raise
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 연결 종료")
    
    def initialize_schema(self):
        """그래프 스키마 초기화"""
        with self.driver.session() as session:
            # 제약조건 생성
            self._create_constraints(session)
            # 인덱스 생성
            self._create_indexes(session)
            logger.info("그래프 스키마 초기화 완료")
    
    def _create_constraints(self, session):
        """유니크 제약조건 생성"""
        constraints = [
            "CREATE CONSTRAINT law_id_unique IF NOT EXISTS FOR (l:Law) REQUIRE l.law_id IS UNIQUE",
            "CREATE CONSTRAINT article_unique IF NOT EXISTS FOR (a:Article) REQUIRE (a.law_id, a.article_number) IS UNIQUE",
            "CREATE CONSTRAINT case_number_unique IF NOT EXISTS FOR (p:Precedent) REQUIRE p.case_number IS UNIQUE",
            "CREATE CONSTRAINT ordinance_unique IF NOT EXISTS FOR (o:Ordinance) REQUIRE (o.region, o.ordinance_number) IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
                logger.debug(f"제약조건 생성: {constraint}")
            except Exception as e:
                logger.warning(f"제약조건 생성 실패: {e}")
    
    def _create_indexes(self, session):
        """검색 성능을 위한 인덱스 생성"""
        indexes = [
            "CREATE INDEX article_content_index IF NOT EXISTS FOR (a:Article) ON (a.content)",
            "CREATE INDEX law_name_index IF NOT EXISTS FOR (l:Law) ON (l.name)",
            "CREATE INDEX ordinance_name_index IF NOT EXISTS FOR (o:Ordinance) ON (o.ordinance_name)",
            "CREATE INDEX precedent_summary_index IF NOT EXISTS FOR (p:Precedent) ON (p.summary)"
        ]
        
        for index in indexes:
            try:
                session.run(index)
                logger.debug(f"인덱스 생성: {index}")
            except Exception as e:
                logger.warning(f"인덱스 생성 실패: {e}")
    
    def create_law_node(self, law_data: Dict) -> str:
        """법령 노드 생성"""
        with self.driver.session() as session:
            query = """
            CREATE (l:Law {
                law_id: $law_id,
                name: $name,
                category: $category,
                effective_date: $effective_date,
                last_updated: $last_updated,
                status: $status,
                created_at: datetime()
            })
            RETURN l.law_id as law_id
            """
            
            result = session.run(query, law_data)
            law_id = result.single()["law_id"]
            logger.info(f"법령 노드 생성: {law_id}")
            return law_id
    
    def create_article_node(self, article_data: Dict) -> str:
        """조문 노드 생성"""
        with self.driver.session() as session:
            query = """
            CREATE (a:Article {
                law_id: $law_id,
                article_number: $article_number,
                content: $content,
                section: $section,
                subsection: $subsection,
                last_updated: $last_updated,
                created_at: datetime()
            })
            RETURN elementId(a) as node_id
            """
            
            result = session.run(query, article_data)
            node_id = result.single()["node_id"]
            logger.info(f"조문 노드 생성: {article_data['article_number']}")
            return str(node_id)
    
    def create_relationship(self, from_node_id: str, to_node_id: str, 
                          rel_type: str, properties: Dict = None) -> bool:
        """노드 간 관계 생성"""
        with self.driver.session() as session:
            if properties is None:
                properties = {}
                
            query = f"""
            MATCH (from_node), (to_node)
            WHERE elementId(from_node) = $from_id AND elementId(to_node) = $to_id
            CREATE (from_node)-[r:{rel_type} $properties]->(to_node)
            RETURN type(r) as relationship_type
            """
            
            result = session.run(query, {
                "from_id": from_node_id,
                "to_id": to_node_id,
                "properties": properties
            })
            
            if result.single():
                logger.info(f"관계 생성: {rel_type}")
                return True
            return False
    
    def search_articles_by_content(self, search_term: str, limit: int = 10) -> List[Dict]:
        """내용으로 조문 검색"""
        with self.driver.session() as session:
            query = """
            MATCH (a:Article)-[:BELONGS_TO]->(l:Law)
            WHERE a.content CONTAINS $search_term
            RETURN a.article_number as article_number,
                   a.content as content,
                   l.name as law_name,
                   a.section as section
            LIMIT $limit
            """
            
            result = session.run(query, {"search_term": search_term, "limit": limit})
            return [dict(record) for record in result]
    
    def get_related_articles(self, article_id: str, depth: int = 2) -> List[Dict]:
        """관련 조문 검색 (관계 기반)"""
        with self.driver.session() as session:
            query = f"""
            MATCH (a:Article)-[*1..{depth}]-(related:Article)
            WHERE elementId(a) = $article_id
            RETURN DISTINCT related.article_number as article_number,
                            related.content as content,
                            related.section as section
            """
            
            result = session.run(query, {"article_id": article_id})
            return [dict(record) for record in result]
    
    def get_law_structure(self, law_id: str) -> Dict:
        """법령의 전체 구조 조회"""
        with self.driver.session() as session:
            query = """
            MATCH (l:Law {law_id: $law_id})
            OPTIONAL MATCH (l)<-[:BELONGS_TO]-(a:Article)
            RETURN l.name as law_name,
                   l.category as category,
                   collect({
                       article_number: a.article_number,
                       content: a.content,
                       section: a.section
                   }) as articles
            """
            
            result = session.run(query, {"law_id": law_id})
            return dict(result.single()) if result.single() else {}
    
    def find_cross_references(self, article_content: str) -> List[Dict]:
        """조문 내 다른 조문 참조 찾기"""
        import re
        
        # 조문 참조 패턴 (제X조, 같은 법 제X조 등)
        reference_patterns = [
            r"제(\d+)조",
            r"같은\s*법\s*제(\d+)조", 
            r"이\s*법\s*제(\d+)조"
        ]
        
        references = []
        for pattern in reference_patterns:
            matches = re.findall(pattern, article_content)
            references.extend([f"제{match}조" for match in matches])
        
        if not references:
            return []
        
        with self.driver.session() as session:
            query = """
            MATCH (a:Article)
            WHERE a.article_number IN $references
            RETURN a.article_number as article_number,
                   a.content as content,
                   elementId(a) as node_id
            """
            
            result = session.run(query, {"references": references})
            return [dict(record) for record in result]


# 사용 예시
if __name__ == "__main__":
    # 그래프 관리자 초기화
    graph_manager = LegalGraphManager()
    
    # 스키마 초기화
    graph_manager.initialize_schema()
    
    # 샘플 데이터 생성
    sample_law = {
        "law_id": "URBAN_REDEVELOPMENT_LAW",
        "name": "도시 및 주거환경정비법",
        "category": "법률",
        "effective_date": "2003-07-01",
        "last_updated": "2023-12-31",
        "status": "시행"
    }
    
    graph_manager.create_law_node(sample_law)
    
    # 연결 종료
    graph_manager.close() 