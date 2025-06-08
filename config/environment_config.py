"""
환경별 설정 관리 모듈
개발, 테스트, 프로덕션 환경에 따른 설정을 자동으로 관리합니다.
"""

import os
import logging
from typing import Dict, Any, Optional
from enum import Enum
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Environment(Enum):
    """환경 타입"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class EnvironmentConfig:
    """환경별 설정 관리 클래스"""
    
    def __init__(self):
        """환경 설정 초기화"""
        load_dotenv()
        self.environment = self._detect_environment()
        self.config = self._load_environment_config()
        logger.info(f"🌍 환경 설정: {self.environment.value}")
    
    def _detect_environment(self) -> Environment:
        """현재 환경 감지"""
        env_str = os.getenv("ENVIRONMENT", "").lower()
        
        # Streamlit Cloud 감지
        if os.getenv("STREAMLIT_SHARING") or "streamlit" in os.getenv("HOME", "").lower():
            return Environment.PRODUCTION
            
        # 테스트 환경 감지
        if "pytest" in os.environ.get("_", "") or os.getenv("TESTING"):
            return Environment.TESTING
            
        # 환경변수 직접 설정
        if env_str in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env_str in ["test", "testing"]:
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """환경별 설정 로드"""
        base_config = self._get_base_config()
        
        if self.environment == Environment.DEVELOPMENT:
            return {**base_config, **self._get_development_config()}
        elif self.environment == Environment.TESTING:
            return {**base_config, **self._get_testing_config()}
        elif self.environment == Environment.PRODUCTION:
            return {**base_config, **self._get_production_config()}
        else:
            return base_config
    
    def _get_base_config(self) -> Dict[str, Any]:
        """모든 환경에 공통적용되는 기본 설정"""
        return {
            "app_name": "도시정비사업 Graph RAG 시스템",
            "version": "1.0.0",
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": os.getenv("LOG_FILE", "logs/system.log")
            },
            "embedding": {
                "model_name": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                "batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
                "device": "cpu"
            },
            "chunking": {
                "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),
                "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50"))
            }
        }
    
    def _get_development_config(self) -> Dict[str, Any]:
        """개발 환경 설정"""
        return {
            "debug": True,
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j")),
                "password": os.getenv("NEO4J_PASSWORD", "password"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
                "connection_timeout": 30,
                "max_connection_lifetime": 3600
            },
            "logging": {
                "level": "DEBUG",
                "console_output": True
            },
            "cache": {
                "enabled": True,
                "ttl": 300  # 5분
            },
            "streamlit": {
                "port": 8501,
                "debug": True,
                "hot_reload": True
            }
        }
    
    def _get_testing_config(self) -> Dict[str, Any]:
        """테스트 환경 설정"""
        return {
            "debug": True,
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USERNAME", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "testpassword"),
                "database": os.getenv("NEO4J_DATABASE", "test"),
                "connection_timeout": 10,
                "max_connection_lifetime": 1800
            },
            "logging": {
                "level": "DEBUG",
                "console_output": True,
                "file": "logs/test.log"
            },
            "cache": {
                "enabled": False
            },
            "embedding": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",  # 빠른 모델
                "batch_size": 16
            }
        }
    
    def _get_production_config(self) -> Dict[str, Any]:
        """프로덕션 환경 설정"""
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
            "debug": False,
            "neo4j": {
                "uri": get_env_var("NEO4J_URI"),
                "username": get_env_var("NEO4J_USERNAME", get_env_var("NEO4J_USER")),
                "password": get_env_var("NEO4J_PASSWORD"),
                "database": get_env_var("NEO4J_DATABASE", "neo4j"),
                "connection_timeout": 60,
                "max_connection_lifetime": 7200
            },
            "logging": {
                "level": "INFO",
                "console_output": False,
                "file": "logs/production.log"
            },
            "cache": {
                "enabled": True,
                "ttl": 3600  # 1시간
            },
            "streamlit": {
                "port": int(os.getenv("PORT", "8501")),
                "debug": False,
                "hot_reload": False
            },
            "performance": {
                "max_workers": 4,
                "timeout": 300,
                "retry_attempts": 3
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        점 표기법으로 설정값 가져오기
        
        Args:
            key_path: "neo4j.uri" 같은 점 표기법 키
            default: 기본값
            
        Returns:
            설정값
            
        Example:
            config.get("neo4j.uri")
            config.get("logging.level", "INFO")
        """
        keys = key_path.split(".")
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def is_development(self) -> bool:
        """개발 환경 여부 확인"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """테스트 환경 여부 확인"""
        return self.environment == Environment.TESTING
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.environment == Environment.PRODUCTION
    
    def validate_config(self) -> bool:
        """설정 유효성 검사"""
        issues = []
        
        # Neo4j 필수 설정 확인
        neo4j_config = self.get("neo4j", {})
        required_neo4j_keys = ["uri", "username", "password"]
        
        for key in required_neo4j_keys:
            if not neo4j_config.get(key):
                issues.append(f"❌ Neo4j {key} 설정이 누락되었습니다")
        
        # Google API 키 확인 (프로덕션에서만)
        if self.is_production():
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                issues.append("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다")
        
        # 로그 디렉토리 확인
        log_file = self.get("logging.file")
        if log_file:
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                    logger.info(f"📁 로그 디렉토리 생성: {log_dir}")
                except Exception as e:
                    issues.append(f"❌ 로그 디렉토리 생성 실패: {e}")
        
        # 결과 출력
        if issues:
            logger.error("설정 검증 실패:")
            for issue in issues:
                logger.error(f"   {issue}")
            return False
        else:
            logger.info("✅ 설정 검증 완료")
            return True
    
    def print_config_summary(self):
        """설정 요약 출력"""
        print(f"\n{'='*50}")
        print(f"🔧 {self.get('app_name')} 설정 요약")
        print(f"{'='*50}")
        print(f"🌍 환경: {self.environment.value}")
        print(f"🔗 Neo4j URI: {self.get('neo4j.uri')}")
        print(f"👤 Neo4j 사용자: {self.get('neo4j.username')}")
        print(f"🗄️ 데이터베이스: {self.get('neo4j.database')}")
        print(f"📊 로깅 레벨: {self.get('logging.level')}")
        print(f"🧠 임베딩 모델: {self.get('embedding.model_name')}")
        print(f"🔍 청크 크기: {self.get('chunking.chunk_size')}")
        print(f"{'='*50}")


# 전역 설정 인스턴스
config = EnvironmentConfig()


def get_config() -> EnvironmentConfig:
    """전역 설정 인스턴스 반환"""
    return config


if __name__ == "__main__":
    # 설정 테스트
    config = EnvironmentConfig()
    config.print_config_summary()
    
    is_valid = config.validate_config()
    print(f"\n설정 유효성: {'✅ 성공' if is_valid else '❌ 실패'}") 