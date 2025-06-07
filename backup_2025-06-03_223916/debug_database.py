#!/usr/bin/env python3
"""
데이터베이스 상태 진단 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph.legal_graph import LegalGraphManager

def main():
    print("🔍 데이터베이스 진단 시작...")
    
    graph_manager = LegalGraphManager()
    
    print('\n📊 현재 데이터베이스 상태:')
    with graph_manager.driver.session() as session:
        # 노드 수 확인
        result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
        for record in result:
            print(f'   {record["labels"]}: {record["count"]}개')
        
        # 관계 확인
        print('\n🔗 관계 상태:')
        result = session.run('MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count')
        relationships = list(result)
        if relationships:
            for record in relationships:
                print(f'   {record["rel_type"]}: {record["count"]}개')
        else:
            print('   ❌ 관계가 하나도 없습니다!')

        # Article-Law 연결 확인
        print('\n🔍 Article-Law 연결 확인:')
        result = session.run('MATCH (a:Article)-[r:BELONGS_TO]->(l:Law) RETURN count(r) as connected_articles')
        for record in result:
            print(f'   연결된 Article: {record["connected_articles"]}개')
        
        # 연결되지 않은 Article 확인
        print('\n❓ 연결되지 않은 Article 확인:')
        result = session.run('''
            MATCH (a:Article) 
            WHERE NOT (a)-[:BELONGS_TO]->(:Law)
            RETURN count(a) as unconnected_articles
        ''')
        for record in result:
            print(f'   연결 안된 Article: {record["unconnected_articles"]}개')
        
        # 샘플 Article 확인
        print('\n📄 샘플 Article 정보:')
        result = session.run('MATCH (a:Article) RETURN a.law_id, a.article_number LIMIT 5')
        for record in result:
            print(f'   Article: {record["a.article_number"]} (Law ID: {record["a.law_id"]})')
        
        # 샘플 Law 확인
        print('\n🏛️ 샘플 Law 정보:')
        result = session.run('MATCH (l:Law) RETURN l.law_id, l.name LIMIT 5')
        for record in result:
            print(f'   Law: {record["l.law_id"]} ({record["l.name"]})')

    graph_manager.close()
    print("\n✅ 진단 완료")

if __name__ == "__main__":
    main() 