#!/usr/bin/env python3
"""
Neo4j 연결 테스트 스크립트
새로운 URI로 직접 연결 테스트
"""

import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


def test_connection():
    # 새로 생성한 인스턴스 정보로 업데이트
    uri = "neo4j+s://b51ef174.databases.neo4j.io"
    user = "neo4j"
    password = "KdPrlE5RT7_Nq8I2DuJzDlPyOPV_HxM-vd8UtDvAdKw"  # 여기를 변경
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        
        with driver.session() as session:
            # 기본 노드 개수 확인
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            count = result.single()["node_count"]
            print(f"✅ 연결 성공! 현재 노드 개수: {count}")
            
            # 간단한 테스트 노드 생성
            session.run("CREATE (test:TestNode {name: 'Hello Neo4j!'})")
            print("✅ 테스트 노드 생성 완료")
            
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    test_connection()
