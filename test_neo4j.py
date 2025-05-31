import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

def test_neo4j_connection():
    # 환경변수 로드
    load_dotenv()
    
    print('=== Neo4j 연결 테스트 ===')
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')
    database = os.getenv('NEO4J_DATABASE')
    
    print(f'URI: {uri}')
    print(f'User: {user}')
    print(f'Password: {password[:10] if password else "None"}...')
    print(f'Database: {database}')
    print()
    
    try:
        # Neo4j 드라이버 생성
        print('드라이버 생성 중...')
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 연결 테스트
        print('연결 테스트 중...')
        with driver.session(database=database) as session:
            result = session.run('RETURN "Hello Neo4j!" as message')
            record = result.single()
            print(f'✅ 연결 성공! 응답: {record["message"]}')
            
            # 간단한 쿼리 실행
            result = session.run('MATCH (n) RETURN count(n) as node_count LIMIT 1')
            count_record = result.single()
            print(f'✅ 노드 개수: {count_record["node_count"]}')
            
        driver.close()
        print('✅ Neo4j 연결 테스트 완료!')
        return True
        
    except Exception as e:
        print(f'❌ Neo4j 연결 실패: {type(e).__name__}: {e}')
        return False

if __name__ == '__main__':
    test_neo4j_connection() 