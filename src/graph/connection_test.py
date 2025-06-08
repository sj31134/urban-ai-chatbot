"""
Neo4j 연결 테스트 및 검증 모듈
시스템 시작 시 데이터베이스 상태를 체크하고 문제를 진단합니다.
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Neo4jConnectionTester:
    """Neo4j 연결 테스트 및 진단 클래스"""
    
    def __init__(self):
        """연결 테스터 초기화"""
        load_dotenv()
        self.driver = None
        self.connection_info = self._get_connection_info()
        
    def _get_connection_info(self) -> Dict[str, str]:
        """환경변수에서 연결 정보 가져오기"""
        def get_env_var(key: str, default: str = "") -> str:
            """환경변수 또는 Streamlit secrets에서 값 가져오기"""
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and key in st.secrets:
                    return str(st.secrets[key])
            except:
                pass
            return os.getenv(key, default)
        
        return {
            "uri": get_env_var("NEO4J_URI", "bolt://localhost:7687"),
            "username": get_env_var("NEO4J_USERNAME", get_env_var("NEO4J_USER", "neo4j")),
            "password": get_env_var("NEO4J_PASSWORD", ""),
            "database": get_env_var("NEO4J_DATABASE", "neo4j")
        }
    
    def test_connection(self, timeout: int = 30) -> Dict[str, any]:
        """
        Neo4j 연결 테스트 수행
        
        Args:
            timeout: 연결 타임아웃 (초)
            
        Returns:
            테스트 결과 딕셔너리
        """
        result = {
            "success": False,
            "error": None,
            "connection_time": None,
            "server_info": None,
            "database_stats": None,
            "recommendations": []
        }
        
        start_time = time.time()
        
        try:
            logger.info("🔍 Neo4j 연결 테스트 시작...")
            logger.info(f"   URI: {self.connection_info['uri']}")
            logger.info(f"   사용자: {self.connection_info['username']}")
            logger.info(f"   데이터베이스: {self.connection_info['database']}")
            
            # 드라이버 생성
            self.driver = GraphDatabase.driver(
                self.connection_info["uri"],
                auth=(self.connection_info["username"], self.connection_info["password"]),
                connection_timeout=timeout,
                max_connection_lifetime=3600
            )
            
            # 연결 검증
            logger.info("   연결 검증 중...")
            self.driver.verify_connectivity()
            
            connection_time = time.time() - start_time
            result["connection_time"] = connection_time
            
            # 서버 정보 수집
            logger.info("   서버 정보 수집 중...")
            result["server_info"] = self._get_server_info()
            
            # 데이터베이스 통계 수집
            logger.info("   데이터베이스 통계 수집 중...")
            result["database_stats"] = self._get_database_stats()
            
            result["success"] = True
            logger.info("✅ Neo4j 연결 테스트 성공!")
            logger.info(f"   연결 시간: {connection_time:.2f}초")
            
        except AuthError as e:
            error_msg = "인증 실패: 사용자명 또는 비밀번호를 확인하세요"
            result["error"] = error_msg
            result["recommendations"].append("NEO4J_USERNAME과 NEO4J_PASSWORD 환경변수를 확인하세요")
            logger.error(f"❌ {error_msg}: {e}")
            
        except ServiceUnavailable as e:
            error_msg = "서비스 연결 불가: Neo4j 서버가 실행 중인지 확인하세요"
            result["error"] = error_msg
            result["recommendations"].extend([
                "NEO4J_URI가 정확한지 확인하세요",
                "Neo4j Aura 인스턴스가 실행 중인지 확인하세요",
                "네트워크 연결을 확인하세요"
            ])
            logger.error(f"❌ {error_msg}: {e}")
            
        except ClientError as e:
            error_msg = f"클라이언트 오류: {e.message}"
            result["error"] = error_msg
            result["recommendations"].append("Neo4j 데이터베이스 설정을 확인하세요")
            logger.error(f"❌ {error_msg}")
            
        except Exception as e:
            error_msg = f"알 수 없는 오류: {e}"
            result["error"] = error_msg
            result["recommendations"].append("시스템 로그를 확인하고 관리자에게 문의하세요")
            logger.error(f"❌ {error_msg}")
            
        finally:
            if self.driver:
                self.driver.close()
                
        return result
    
    def _get_server_info(self) -> Dict[str, any]:
        """서버 정보 수집"""
        try:
            with self.driver.session() as session:
                # Neo4j 버전 확인
                version_result = session.run("CALL dbms.components() YIELD name, versions")
                components = [dict(record) for record in version_result]
                
                # 데이터베이스 목록
                db_result = session.run("SHOW DATABASES")
                databases = [dict(record) for record in db_result]
                
                return {
                    "components": components,
                    "databases": databases,
                    "server_time": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.warning(f"서버 정보 수집 실패: {e}")
            return {"error": str(e)}
    
    def _get_database_stats(self) -> Dict[str, any]:
        """데이터베이스 통계 수집"""
        try:
            with self.driver.session(database=self.connection_info["database"]) as session:
                # 노드 통계
                node_stats = {}
                node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                for record in node_result:
                    labels = record["labels"]
                    if labels:
                        key = ":".join(sorted(labels))
                        node_stats[key] = record["count"]
                
                # 관계 통계
                rel_stats = {}
                rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                for record in rel_result:
                    rel_stats[record["type"]] = record["count"]
                
                # 전체 통계
                total_result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                total_nodes = total_result.single()["total_nodes"]
                
                total_rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
                total_relationships = total_rel_result.single()["total_relationships"]
                
                return {
                    "nodes": node_stats,
                    "relationships": rel_stats,
                    "total_nodes": total_nodes,
                    "total_relationships": total_relationships
                }
                
        except Exception as e:
            logger.warning(f"데이터베이스 통계 수집 실패: {e}")
            return {"error": str(e)}
    
    def diagnose_connection_issues(self) -> List[str]:
        """연결 문제 진단 및 해결책 제안"""
        recommendations = []
        
        # 환경변수 체크
        if not self.connection_info["uri"]:
            recommendations.append("❌ NEO4J_URI 환경변수가 설정되지 않았습니다")
        
        if not self.connection_info["username"]:
            recommendations.append("❌ NEO4J_USERNAME 환경변수가 설정되지 않았습니다")
        
        if not self.connection_info["password"]:
            recommendations.append("❌ NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")
        
        # URI 형식 체크
        uri = self.connection_info["uri"]
        if uri and not (uri.startswith("neo4j://") or uri.startswith("neo4j+s://") or uri.startswith("bolt://")):
            recommendations.append("⚠️ NEO4J_URI 형식을 확인하세요 (neo4j+s://, neo4j://, bolt://)")
        
        return recommendations
    
    def print_test_results(self, result: Dict[str, any]):
        """테스트 결과를 보기 좋게 출력"""
        print("\n" + "="*60)
        print("🔍 Neo4j 연결 테스트 결과")
        print("="*60)
        
        if result["success"]:
            print("✅ 연결 상태: 성공")
            print(f"⏱️  연결 시간: {result['connection_time']:.2f}초")
            
            if result["database_stats"]:
                stats = result["database_stats"]
                print(f"\n📊 데이터베이스 통계:")
                print(f"   전체 노드: {stats.get('total_nodes', 0):,}개")
                print(f"   전체 관계: {stats.get('total_relationships', 0):,}개")
                
                if stats.get('nodes'):
                    print(f"\n📄 노드 유형별 통계:")
                    for node_type, count in stats['nodes'].items():
                        print(f"   {node_type}: {count:,}개")
                
                if stats.get('relationships'):
                    print(f"\n🔗 관계 유형별 통계:")
                    for rel_type, count in stats['relationships'].items():
                        print(f"   {rel_type}: {count:,}개")
        else:
            print("❌ 연결 상태: 실패")
            print(f"🚨 오류: {result['error']}")
            
            if result["recommendations"]:
                print(f"\n💡 해결책:")
                for rec in result["recommendations"]:
                    print(f"   • {rec}")
        
        print("="*60)


def test_neo4j_connection():
    """간단한 연결 테스트 함수"""
    tester = Neo4jConnectionTester()
    
    # 연결 문제 사전 진단
    issues = tester.diagnose_connection_issues()
    if issues:
        print("⚠️ 사전 진단에서 다음 문제가 발견되었습니다:")
        for issue in issues:
            print(f"   {issue}")
        print()
    
    # 연결 테스트 실행
    result = tester.test_connection()
    
    # 결과 출력
    tester.print_test_results(result)
    
    return result["success"]


if __name__ == "__main__":
    success = test_neo4j_connection()
    sys.exit(0 if success else 1) 