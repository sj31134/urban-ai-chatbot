#!/usr/bin/env python3
"""
누락된 Article-Law BELONGS_TO 관계 복구 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager

def fix_relationships():
    print("🔧 Article-Law 관계 복구 시작...")
    
    graph_manager = LegalGraphManager()
    
    with graph_manager.driver.session() as session:
        
        # 1. 현재 상태 확인
        print("\n📊 복구 전 상태:")
        result = session.run("MATCH (a:Article) RETURN count(a) as total_articles")
        total_articles = list(result)[0]["total_articles"]
        print(f"   총 Article: {total_articles}개")
        
        result = session.run("MATCH (l:Law) RETURN count(l) as total_laws")
        total_laws = list(result)[0]["total_laws"]
        print(f"   총 Law: {total_laws}개")
        
        # 2. Article-Law 매칭 및 관계 생성
        print("\n🔗 BELONGS_TO 관계 생성 중...")
        
        # law_id가 같은 Article과 Law를 매칭하여 관계 생성
        query = """
        MATCH (a:Article), (l:Law)
        WHERE a.law_id = l.law_id
        AND NOT EXISTS((a)-[:BELONGS_TO]->(l))
        CREATE (a)-[:BELONGS_TO]->(l)
        RETURN count(*) as created_relationships
        """
        
        result = session.run(query)
        created_count = list(result)[0]["created_relationships"]
        print(f"   생성된 관계: {created_count}개")
        
        # 3. 결과 확인
        print("\n✅ 복구 후 상태:")
        result = session.run("MATCH (a:Article)-[:BELONGS_TO]->(l:Law) RETURN count(*) as connected_articles")
        connected_articles = list(result)[0]["connected_articles"]
        print(f"   연결된 Article: {connected_articles}개")
        
        result = session.run("""
            MATCH (a:Article) 
            WHERE NOT (a)-[:BELONGS_TO]->(:Law)
            RETURN count(a) as unconnected_articles
        """)
        unconnected_articles = list(result)[0]["unconnected_articles"]
        print(f"   연결 안된 Article: {unconnected_articles}개")
        
        # 4. 관계 타입 확인
        print("\n🔗 관계 현황:")
        result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
        for record in result:
            print(f"   {record['rel_type']}: {record['count']}개")
        
        # 5. 샘플 확인
        print("\n📄 샘플 연결 확인:")
        result = session.run("""
            MATCH (a:Article)-[:BELONGS_TO]->(l:Law)
            RETURN a.article_number, a.law_id, l.name
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['a.article_number']} -> {record['l.name']} (ID: {record['a.law_id']})")
    
    graph_manager.close()
    print("\n✅ 관계 복구 완료!")

if __name__ == "__main__":
    fix_relationships() 