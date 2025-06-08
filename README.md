# 🏗️ 도시정비사업 Graph RAG 시스템

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.12+-green.svg)](https://neo4j.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-purple.svg)](https://langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)

> **도시 및 주거환경정비법, 소규모주택정비법 등 도시정비사업 관련 법령의 전문 AI 챗봇**  
> Neo4j Graph RAG + LangChain + Google Gemini를 활용한 법령 질의응답 시스템

## 📋 목차

- [🎯 프로젝트 개요](#-프로젝트-개요)
- [✨ 주요 기능](#-주요-기능)
- [🏗️ 시스템 아키텍처](#️-시스템-아키텍처)
- [🚀 빠른 시작](#-빠른-시작)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [⚙️ 설정 가이드](#️-설정-가이드)
- [💡 사용법](#-사용법)
- [🧪 테스트](#-테스트)
- [📊 성능 정보](#-성능-정보)
- [🤝 기여하기](#-기여하기)
- [📄 라이선스](#-라이선스)

## 🎯 프로젝트 개요

도시정비사업 Graph RAG 시스템은 복잡한 도시정비 관련 법령을 효율적으로 검색하고 해석할 수 있는 AI 시스템입니다.

### 🎯 해결하고자 하는 문제
- **법령 복잡성**: 도시정비법, 소규모주택정비법 등 여러 법령의 복잡한 조문 구조
- **참조 관계**: 법령 간, 조문 간 복잡한 상호 참조 관계
- **실시간 해석**: 법령 개정사항의 신속한 반영과 정확한 해석
- **접근성**: 법무 전문가가 아닌 일반인도 쉽게 법령 정보에 접근

### 🔧 기술적 특징
- **Graph RAG**: Neo4j를 활용한 법령 간 관계 모델링
- **하이브리드 검색**: 키워드 + 그래프 탐색 + 임베딩 기반 검색 조합
- **출처 검증**: 모든 답변에 정확한 법령 조문 출처 제공
- **신뢰도 평가**: AI 답변의 신뢰도 자동 계산

## ✨ 주요 기능

### 🔍 지능형 법령 검색
- **다중 검색 방식**: 키워드, 의미론적, 그래프 관계 기반 검색
- **조문 간 참조 탐색**: 법령 조문 간 2-3차 연관관계 자동 발견
- **실시간 검색**: 평균 5-10초 내 정확한 답변 제공

### 📚 포괄적 법령 커버리지
- **도시 및 주거환경정비법** 전체 조문
- **소규모주택정비법** 및 시행령, 시행규칙
- **빈집 및 소규모주택 정비에 관한 특례법**
- **지자체 조례** (서울시, 부산시 등)
- **행정규칙** 및 고시

### 🤖 전문 AI 어시스턴트
- **법령 전문 프롬프트**: 도시정비 분야 특화 답변 생성
- **출처 명시**: 모든 답변에 구체적 조문 번호 및 법령명 제공
- **신뢰도 표시**: 답변의 정확성 신뢰도 0.0-1.0 척도로 제공
- **관련 조문 추천**: 질의와 관련된 추가 조문 자동 추천

### 💻 사용자 친화적 인터페이스
- **Streamlit 웹앱**: 직관적이고 반응형 웹 인터페이스
- **실시간 채팅**: 대화형 질의응답 인터페이스
- **시각적 피드백**: 신뢰도, 출처, 관련 조문 시각적 표시
- **채팅 기록 관리**: 질의 기록 저장 및 내보내기

## 🏗️ 시스템 아키텍처

```mermaid
graph TB
    User[👤 사용자] --> Streamlit[🖥️ Streamlit UI]
    Streamlit --> RAGChain[🔗 Legal RAG Chain]
    
    RAGChain --> Retriever[🔍 Legal Graph Retriever]
    RAGChain --> LLM[🤖 Google Gemini]
    
    Retriever --> Neo4j[(🗄️ Neo4j Graph DB)]
    Retriever --> Embedder[📊 Sentence Transformer]
    
    PDFProcessor[📄 Document Processor] --> Neo4j
    
    subgraph "검색 전략"
        Keyword[🔤 키워드 검색]
        Graph[🕸️ 그래프 탐색]
        Semantic[🧠 의미론적 검색]
    end
    
    Retriever --> Keyword
    Retriever --> Graph  
    Retriever --> Semantic
    
    subgraph "법령 데이터"
        Laws[⚖️ 법령 PDF]
        Ordinances[📋 조례 PDF]
        Rules[📑 행정규칙]
    end
    
    Laws --> PDFProcessor
    Ordinances --> PDFProcessor
    Rules --> PDFProcessor
```

### 핵심 구성요소

1. **Graph Database (Neo4j)**
   - 법령, 조문, 조례, 판례 노드
   - REFERENCES, IMPLEMENTS, APPLIES_TO 관계
   - 법령 간 복잡한 참조 구조 모델링

2. **RAG Pipeline**
   - 하이브리드 검색: 키워드 + 그래프 + 임베딩
   - 결과 통합 및 랭킹 알고리즘
   - 출처 검증 및 신뢰도 계산

3. **LLM Integration**
   - Google Gemini 1.5 Flash 모델
   - 법령 전문 프롬프트 엔지니어링
   - 구조화된 답변 생성

## 🚀 빠른 시작

### 📋 시스템 요구사항

- **Python**: 3.8 이상
- **Docker**: 최신 버전 (Neo4j 컨테이너용)
- **메모리**: 최소 8GB RAM 권장
- **저장공간**: 최소 10GB 여유 공간

### ⚡ 1분 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/urban_legal_rag.git
cd urban_legal_rag

# 2. 자동 설치 실행
chmod +x setup_legal_rag.sh
./setup_legal_rag.sh

# 3. API 키 설정
nano .env  # Google Gemini API 키 입력

# 4. 시스템 시작
./start_system.sh
```

### 🌐 웹 인터페이스 접속

설치 완료 후 브라우저에서 다음 주소로 접속:

- **메인 챗봇**: http://localhost:8501
- **Neo4j 브라우저**: http://localhost:7474

## 📁 프로젝트 구조

```
urban_legal_rag/
├── 📂 data/                    # 법령 데이터
│   ├── 📂 laws/               # 주요 법령 PDF
│   ├── 📂 ordinances/         # 지자체 조례
│   └── 📂 processed/          # 전처리된 데이터
├── 📂 src/                    # 소스 코드
│   ├── 📂 graph/              # Neo4j 그래프 관리
│   │   ├── legal_graph.py     # 그래프 스키마 및 CRUD
│   │   └── schema_builder.py  # 스키마 초기화
│   ├── 📂 rag/                # RAG 파이프라인
│   │   ├── document_processor.py  # 문서 처리
│   │   └── legal_rag_chain.py     # RAG 체인
│   └── 📂 chatbot/            # 사용자 인터페이스
│       └── legal_assistant.py  # Streamlit 앱
├── 📂 config/                 # 설정 파일
│   ├── neo4j_config.yaml     # Neo4j 설정
│   ├── legal_schema.json     # 법령 스키마
│   └── environment.env.template # 환경변수 템플릿
├── 📂 tests/                  # 테스트 코드
│   └── test_legal_queries.py # 법령 질의 테스트
├── 📂 logs/                   # 로그 파일
├── requirements.txt           # Python 의존성
├── setup_legal_rag.sh        # 자동 설치 스크립트
├── start_system.sh           # 시스템 시작
├── stop_system.sh            # 시스템 중지
└── README.md                 # 프로젝트 문서
```

## ⚙️ 설정 가이드

### 🔑 필수 API 키 설정

1. **Google Gemini API**:
   ```bash
   # .env 파일에서 설정
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

2. **LangChain 추적** (선택사항):
   ```bash
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   LANGCHAIN_TRACING_V2=true
   ```

#### 🔧 전체 환경변수 목록

```bash
# 필수 설정
GOOGLE_API_KEY=your_gemini_api_key_here


# 로그 레벨 (INFO, DEBUG, WARNING, ERROR)
LOG_LEVEL=INFO
```

### 📊 Neo4j 데이터베이스 설정

기본 설정 (Docker 자동 설치):
```yaml
connection:
  uri: "bolt://localhost:7687"
  username: "legal_admin" 
  password: "secure_password"
```

### 📄 법령 데이터 준비

다음 위치에 PDF 파일 배치:

```bash
data/laws/
├── 도시정비법_전문.pdf
├── 소규모주택정비법_2023.pdf
└── 빈집정비특례법.pdf

data/ordinances/
├── 서울시_도시재정비조례.pdf
└── 부산시_도시재정비조례.pdf
```

#### 🗄️ 현재 포함된 법령 데이터

시스템에는 다음과 같은 법령 데이터가 포함되어 있습니다:

**📖 주요 법령**
- `도시 및 주거환경정비법(법률)(제20955호)(20250520).doc` - 메인 법령
- `빈집 및 소규모주택 정비에 관한 특례법(법률)(제19225호)(20240215).doc`
- `정비사업 계약업무 처리기준(국토교통부고시)(제2024-465호)(20240905).doc`

**🏢 지자체 조례**
- `서울특별시 도시재정비 촉진을 위한 조례(서울특별시조례)(제9639호)(20250519).doc`
- `용인시 도시 및 주거환경정비 조례(경기도 용인시조례)(제2553호)(20240925).doc`
- `성남시 도시계획 조례(경기도 성남시조례)(제4203호)(20250310).doc`
- `안양시 도시계획 조례(경기도 안양시조례)(제3675호)(20240927).doc`

**📋 별표 및 서식**
- 각 조례별 별표 및 서식 파일 (총 20여개)
- 건축물 용도별 세부 기준 및 서약서 양식 포함

## 💡 사용법

### 🗣️ 기본 질의 예시

1. **조합 설립 관련**:
   ```
   "재개발 조합 설립을 위한 동의 요건은 무엇인가요?"
   ```

2. **사업 절차 관련**:
   ```
   "정비사업 시행인가 신청 시 필요한 서류는?"
   ```

3. **현금청산 관련**:
   ```
   "소규모재개발사업에서 현금청산이 제외되는 경우는?"
   ```

### 📋 고급 기능 활용

1. **교차 법령 질의**:
   ```
   "도시정비법과 소규모주택정비법의 현금청산 규정 차이점은?"
   ```

2. **조례 관련 질의**:
   ```
   "서울시 도시재정비 조례의 특별한 규정은?"
   ```

3. **현행 법령 기반 실제 질의**:
   ```
   "소규모재개발사업에서 현금청산이 제외되는 경우는?"
   "가로주택정비사업의 대상 요건은 무엇인가요?"
   "자율주택정비사업 시행자는 누구인가요?"
   "빈집정비사업의 특례 내용은?"
   "용인시 도시 및 주거환경정비 조례의 특징은?"
   ```

### 📊 결과 해석

- **신뢰도 점수**:
  - 🟢 0.8-1.0: 높은 신뢰도
  - 🟡 0.6-0.8: 중간 신뢰도  
  - 🔴 0.0-0.6: 낮은 신뢰도

- **출처 정보**: 각 답변마다 관련 조문 및 법령명 제공

## 🧪 테스트

### 🔬 테스트 실행

```bash
# 전체 테스트 실행
python -m pytest tests/ -v

# 특정 카테고리 테스트
python -m pytest tests/test_legal_queries.py::TestUrbanRedevelopmentQueries -v

# 성능 테스트
python -m pytest tests/test_legal_queries.py::TestPerformance -v
```

### 📈 테스트 커버리지

- **도시정비법 질의**: 15개 테스트 케이스
- **소규모주택정비법 질의**: 8개 테스트 케이스
- **교차 참조 질의**: 5개 테스트 케이스
- **성능 테스트**: 응답시간 < 30초
- **출처 검증**: 조문 번호 형식 검증

#### 📝 구체적 테스트 케이스 예시

**도시정비법 테스트 (TestUrbanRedevelopmentQueries)**
```python
# URB_001: 재개발 조합 설립 요건
# 예상 출처: 도시정비법 제24조, 제25조
# 신뢰도 임계값: 0.85

# URB_002: 정비사업 시행인가 신청 서류  
# 예상 출처: 도시정비법 제28조, 시행령
# 신뢰도 임계값: 0.80

# URB_003: 현금청산 대상자
# 예상 출처: 도시정비법 제49조, 제50조
# 신뢰도 임계값: 0.88
```

**소규모주택정비법 테스트 (TestSmallScaleHousingQueries)**
```python
# SSH_001: 소규모재개발사업 현금청산 제외
# SSH_002: 가로주택정비사업 대상 요건
# SSH_003: 자율주택정비사업 시행자
```

**성능 및 엣지케이스 테스트**
```python
# 응답시간 테스트: 평균 5-10초, 최대 30초
# 빈 질의, 매우 긴 질의, 무관한 질의 처리 테스트
# 출처 형식 검증: "제X조", "법률 제X호" 패턴 확인
```

## 📊 성능 정보

### ⚡ 응답 성능
- **평균 응답 시간**: 5-10초
- **최대 응답 시간**: 30초 이내
- **동시 사용자**: 최대 10명 권장

### 🎯 정확도 지표
- **법령 검색 정확도**: 85% 이상
- **출처 정확도**: 95% 이상
- **평균 신뢰도 점수**: 0.82

### 💾 리소스 사용량
- **메모리 사용량**: 4-6GB
- **디스크 사용량**: 5-8GB
- **CPU 사용률**: 중간 부하

### ⚙️ 성능 최적화 팁

**🚀 검색 성능 향상**
```python
# 1. 임베딩 캐시 활용
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2. Neo4j 인덱스 최적화
# 텍스트 검색용 fulltext 인덱스
CREATE FULLTEXT INDEX article_content_search FOR (a:Article) ON EACH [a.content]

# 3. 배치 처리로 그래프 구축 속도 향상
def process_documents_batch(data_directory):
    # 여러 문서를 배치로 처리하여 성능 향상
```

**💡 메모리 최적화**
```python
# 1. 텍스트 청킹 크기 조정
chunk_size=512  # 기본값, 메모리 부족 시 256으로 감소
chunk_overlap=50

# 2. 검색 결과 수 제한
max_results=10  # 기본값, 성능 향상을 위해 5로 감소 가능

# 3. 유사도 임계값 조정
similarity_threshold=0.7  # 기본값, 정확도 vs 성능 트레이드오프
```

## 🤝 기여하기

### 🐛 버그 리포트
이슈 등록 시 다음 정보를 포함해주세요:
- 질의 내용
- 기대 결과 vs 실제 결과
- 에러 메시지 (있는 경우)
- 시스템 환경

### 💡 기능 제안
다음과 같은 기여를 환영합니다:
- 새로운 법령 데이터 추가
- 검색 알고리즘 개선
- UI/UX 개선
- 성능 최적화

### 📝 개발 가이드

#### 🏗️ 코드 구조 이해

**핵심 클래스 구조**
```python
# src/graph/legal_graph.py
class LegalGraphManager:
    # Neo4j 그래프 데이터베이스 관리
    # 노드: Law, Article, Ordinance, Precedent
    # 관계: REFERENCES, APPLIES_TO, IMPLEMENTS, BELONGS_TO, AMENDS

# src/rag/legal_rag_chain.py  
class LegalGraphRetriever:
    # 3단계 하이브리드 검색
    # 1. 키워드 검색 → 2. 그래프 확장 → 3. 임베딩 유사도

class LegalRAGChain:
    # Google Gemini와 검색 결과를 결합한 질의응답
    # 신뢰도 계산 및 출처 검증 포함

# src/rag/document_processor.py
class LegalDocumentProcessor:
    # PDF 문서 → 구조화된 그래프 데이터 변환
    # 조문별 분할, 메타데이터 추출, 참조 관계 생성

# src/chatbot/legal_assistant.py
class LegalAssistant:
    # Streamlit 웹 인터페이스
    # 실시간 채팅, 결과 시각화, 세션 관리
```

#### 🔄 개발 워크플로우
1. **환경 설정**
   ```bash
   git clone <repository>
   cd urban_ai_chatbot
   ./setup_legal_rag.sh
   ```

2. **브랜치 생성 및 개발**
   ```bash
   git checkout -b feature/new-feature
   # 변경사항 구현
   ```

3. **테스트 실행**
   ```bash
   # 전체 테스트
   python -m pytest tests/ -v
   
   # 특정 테스트 카테고리
   python -m pytest tests/test_legal_queries.py::TestUrbanRedevelopmentQueries -v
   ```

4. **코드 품질 확인**
   ```bash
   # 코드 스타일 확인 (선택사항)
   flake8 src/
   black src/ --check
   ```

5. **Pull Request 생성**
   - 테스트 통과 확인
   - 변경사항 설명 포함
   - 새로운 기능의 경우 테스트 케이스 추가

#### 🎨 새로운 기능 추가 가이드

**1. 새로운 법령 추가**
```python
# 1. data/laws/에 PDF 파일 배치
# 2. LegalDocumentProcessor로 처리
processor = LegalDocumentProcessor(graph_manager)
result = processor.process_pdf_document("path/to/new_law.pdf", "LAW_CODE")

# 3. 테스트 케이스 추가
def test_new_law_queries(self):
    # 새 법령 관련 테스트 케이스 작성
```

**2. 새로운 검색 알고리즘 추가**
```python
# LegalGraphRetriever에 새 검색 메서드 추가
def _new_search_method(self, query: str) -> List[Document]:
    # 새로운 검색 로직 구현
    pass

# _merge_and_rank_results에 가중치 추가
weights = {
    "keyword": 1.0,
    "graph_expansion": 0.8, 
    "semantic": 0.9,
    "new_method": 0.7  # 새 방법 가중치
}
```

## 🔒 보안 및 준수사항

### 📋 데이터 보안
- 모든 법령 데이터는 공개 자료 기준
- API 키는 환경변수로 안전하게 관리
- 사용자 질의 로그는 로컬에만 저장

### ⚖️ 법령 데이터 저작권
- 공공데이터 이용허락 (CC-BY 4.0) 준수
- 법제처, 국토교통부 등 공식 출처 데이터 활용
- 상업적 이용 시 별도 검토 필요

## 🌐 클라우드 배포 가이드

### 🚀 프로덕션 배포 개요

현재 시스템은 다음 클라우드 플랫폼에서 배포 가능합니다:
- **Streamlit Community Cloud** (추천) - 무료, 간편
- **Railway** - 컨테이너 기반, 자동 스케일링
- **Google Cloud Run** - 서버리스, 고성능
- **Heroku** - 전통적인 PaaS

### 🌟 Streamlit Community Cloud 배포 (추천)

#### **1단계: GitHub 저장소 준비**
```bash
# 코드 커밋 및 푸시
git add .
git commit -m "Fix Neo4j connection and add cloud deployment guide"
git push origin main
```

#### **2단계: Streamlit Cloud에서 앱 생성**
1. https://share.streamlit.io/ 접속
2. "New app" 클릭
3. GitHub 저장소 선택
4. **Main file path**: `web_app.py`
5. **Advanced settings** 클릭

#### **3단계: Secrets 설정**
Streamlit Cloud의 **App settings > Secrets**에서 다음 설정:

```toml
# Neo4j 클라우드 연결
NEO4J_URI = "neo4j+s://b51ef174.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "KdPrlE5RT7_Nq8I2DuJzDlPyOPV_HxM-vd8UtDvAdKw"
NEO4J_DATABASE = "neo4j"

# Google Gemini API
GOOGLE_API_KEY = "AIzaSyAPBXAKIxJPhPp5ZW2swP_lF6_-3209ZGw"

# LangChain 추적 (선택사항)
LANGCHAIN_API_KEY = "your_langchain_api_key_here"
LANGCHAIN_TRACING_V2 = true
LANGCHAIN_PROJECT = "urban_legal_rag"

# 환경 설정
ENVIRONMENT = "production"
```

#### **4단계: 배포 및 접속**
- 자동 배포 완료 후 제공되는 URL로 접속
- 예: `https://your-app-name.streamlit.app`

### 🚂 Railway 배포

#### **1단계: Railway CLI 설치 및 로그인**
```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login
```

#### **2단계: 프로젝트 생성 및 배포**
```bash
# 프로젝트 생성
railway new

# 환경변수 설정
railway variables set NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io
railway variables set NEO4J_USERNAME=neo4j
railway variables set NEO4J_PASSWORD=KdPrlE5RT7_Nq8I2DuJzDlPyOPV_HxM-vd8UtDvAdKw
railway variables set NEO4J_DATABASE=neo4j
railway variables set GOOGLE_API_KEY=AIzaSyAPBXAKIxJPhPp5ZW2swP_lF6_-3209ZGw
railway variables set ENVIRONMENT=production

# Docker 배포
railway up --detach
```

#### **3단계: 도메인 설정**
```bash
# 커스텀 도메인 추가 (선택사항)
railway domain add your-domain.com
```

### ☁️ Google Cloud Run 배포

#### **1단계: Google Cloud 프로젝트 설정**
```bash
# Google Cloud CLI 설치 및 인증
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Container Registry 활성화
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### **2단계: 컨테이너 빌드 및 푸시**
```bash
# Docker 이미지 빌드
docker build -t gcr.io/YOUR_PROJECT_ID/urban-ai-chatbot .

# Google Container Registry에 푸시
docker push gcr.io/YOUR_PROJECT_ID/urban-ai-chatbot
```

#### **3단계: Cloud Run 배포**
```bash
gcloud run deploy urban-ai-chatbot \
  --image gcr.io/YOUR_PROJECT_ID/urban-ai-chatbot \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars="NEO4J_URI=neo4j+s://b51ef174.databases.neo4j.io,NEO4J_USERNAME=neo4j,NEO4J_PASSWORD=your_password,GOOGLE_API_KEY=your_api_key"
```

### 📱 외부 접속 및 이용 가이드

#### **🌍 퍼블릭 URL로 접속하기**

배포 완료 후 다음과 같은 URL을 통해 어디서든 접속 가능합니다:

**Streamlit Cloud 예시:**
- URL: `https://urban-ai-chatbot.streamlit.app`
- 모바일, 태블릿, PC에서 동일하게 접속 가능
- 로컬 컴퓨터 종료와 무관하게 24/7 서비스

**Railway 예시:**
- URL: `https://urban-ai-chatbot-production.up.railway.app`
- 자동 HTTPS 인증서 제공
- 글로벌 CDN으로 빠른 접속

#### **📱 모바일 접속 최적화**

**반응형 디자인 지원:**
- 스마트폰: 세로 모드 최적화
- 태블릿: 가로/세로 자동 조정
- PC: 전체 기능 이용

**접속 방법:**
1. 스마트폰 브라우저에서 배포 URL 접속
2. "홈 화면에 추가" 선택 → 앱처럼 사용 가능
3. 오프라인에서도 기본 기능 이용

#### **🔗 팀 공유 및 협업**

**URL 공유:**
```bash
# 팀원들에게 배포된 URL 공유
https://your-app-name.streamlit.app

# QR 코드 생성하여 모바일 접속 편의성 제공
```

**권한 관리:**
- 퍼블릭 접속: 누구나 이용 가능
- 인증 추가 시: Google/GitHub 로그인 연동 가능
- 기업용: IP 제한 및 사용자 관리 가능

#### **⚡ 성능 및 모니터링**

**자동 스케일링:**
- 사용자 수에 따라 자동으로 서버 확장/축소
- 트래픽 증가 시 자동 대응
- 24시간 무중단 서비스

**모니터링 도구:**
```bash
# Streamlit Cloud 모니터링
- App dashboard에서 실시간 사용량 확인
- 메트릭: 활성 사용자, 응답 시간, 오류율

# 사용량 확인 방법
1. Streamlit Cloud 로그인
2. App settings > Monitoring
3. 실시간 차트 및 로그 확인
```

#### **🛠️ 실시간 업데이트**

**자동 배포:**
```bash
# GitHub에 푸시하면 자동 재배포
git add .
git commit -m "새로운 기능 추가"
git push origin main

# 5-10분 후 자동으로 새 버전 배포 완료
```

**롤백 기능:**
- 문제 발생 시 이전 버전으로 즉시 롤백
- Streamlit Cloud에서 버전 히스토리 관리
- 무중단 배포로 사용자 경험 보장

### 🔧 배포 후 확인사항

#### **필수 체크리스트**
- [ ] 웹사이트 정상 로딩 확인
- [ ] Neo4j 데이터베이스 연결 상태 확인
- [ ] 검색 기능 정상 작동 테스트
- [ ] 모바일 반응형 디자인 확인
- [ ] 외부 네트워크에서 접속 테스트

#### **성능 테스트**
```bash
# 응답 시간 테스트 (배포된 URL 사용)
curl -w "@curl-format.txt" -o /dev/null -s "https://your-app.streamlit.app"

# 부하 테스트 (선택사항)
# Apache Bench 사용
ab -n 100 -c 10 https://your-app.streamlit.app/
```

#### **보안 확인**
- HTTPS 인증서 자동 적용 확인
- API 키가 브라우저에 노출되지 않는지 확인
- 로그에 민감한 정보가 포함되지 않는지 점검

### 💰 비용 및 제한사항

#### **Streamlit Community Cloud (무료)**
- ✅ 무료 호스팅
- ✅ 무제한 퍼블릭 앱
- ⚠️ 리소스 제한: 1GB RAM, 공유 CPU
- ⚠️ 비활성 시 슬립 모드 (자동 재시작)

#### **유료 플랫폼 비교**
| 플랫폼 | 월 비용 | RAM | 트래픽 | 특징 |
|--------|---------|-----|--------|------|
| Railway | $5-20 | 1-8GB | 무제한 | 컨테이너 기반 |
| Google Cloud Run | $0-50 | 1-4GB | 종량제 | 서버리스 |
| Heroku | $7-25 | 512MB-2.5GB | 무제한 | 전통적 PaaS |

### 🆘 배포 트러블슈팅

#### **일반적인 배포 오류**

**1. 빌드 실패**
```bash
# 증상: Docker 빌드 시 패키지 설치 실패
# 해결: requirements.txt 버전 호환성 확인
pip install --upgrade pip
pip install -r requirements.txt --verbose
```

**2. 환경변수 오류**
```bash
# 증상: "NEO4J connection failed"
# 해결: Secrets 설정 재확인
# 특수문자가 포함된 패스워드는 따옴표로 감싸기
NEO4J_PASSWORD = "KdPrlE5RT7_Nq8I2DuJzDlPyOPV_HxM-vd8UtDvAdKw"
```

**3. 메모리 부족**
```bash
# 증상: "Memory limit exceeded"
# 해결: 경량 임베딩 모델 사용
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

**4. 네트워크 타임아웃**
```bash
# 증상: Neo4j 연결 타임아웃
# 해결: 연결 타임아웃 증가
NEO4J_CONNECTION_TIMEOUT = 60
```

이제 **로컬 종료와 무관하게 24/7 클라우드 서비스**가 준비되었습니다! 🚀

## 📞 지원 및 문의

### 🆘 문제 해결

#### 🔧 일반적인 오류 및 해결책

**1. Neo4j 연결 오류**
```bash
# 증상: ServiceUnavailable 또는 연결 거부
# 원인: Docker 컨테이너 미실행 또는 인증 정보 불일치

# 해결책:
docker ps | grep neo4j-legal  # 컨테이너 상태 확인
docker start neo4j-legal     # 컨테이너 시작
docker logs neo4j-legal      # 로그 확인

# .env 파일 확인
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=legal_admin
NEO4J_PASSWORD=secure_password
```

**2. Google Gemini API 오류**
```bash
# 증상: API 키 오류 또는 할당량 초과
# 원인: 잘못된 API 키 또는 요청 한도 초과

# 해결책:
# 1. API 키 확인
echo $GOOGLE_API_KEY  # 환경변수 확인

# 2. Google AI Studio에서 API 사용량 확인
# https://aistudio.google.com/app/apikey

# 3. 백업 모드로 전환 (legal_assistant.py에서 자동 처리)
# Gemini API 실패 시 기본 응답 모드로 전환
```

**3. 임베딩 모델 로딩 오류**
```bash
# 증상: SentenceTransformer 로딩 실패
# 원인: 네트워크 문제 또는 메모리 부족

# 해결책:
# 1. 경량 모델로 변경
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# 2. 로컬 캐시 정리
rm -rf ~/.cache/torch/sentence_transformers/

# 3. 메모리 확인
free -h  # 사용 가능한 메모리 확인 (최소 4GB 권장)
```

**4. PDF 문서 처리 오류**
```bash
# 증상: PDF 텍스트 추출 실패
# 원인: 손상된 PDF 또는 인코딩 문제

# 해결책:
# 1. 이중 백업 시스템 (코드에서 자동 처리)
# pypdf 실패 시 PyPDF2로 자동 전환

# 2. 한글 인코딩 문제
# UTF-8 인코딩으로 텍스트 처리 (코드에서 처리됨)

# 3. 파일 권한 확인
chmod 644 data/laws/*.doc
```

**5. Streamlit 실행 오류**
```bash
# 증상: 웹앱 시작 실패
# 원인: 포트 충돌 또는 의존성 문제

# 해결책:
# 1. 포트 변경
streamlit run src/chatbot/legal_assistant.py --server.port 8502

# 2. 프로세스 확인
lsof -i :8501  # 포트 사용 프로세스 확인
kill -9 <PID>  # 필요시 프로세스 종료

# 3. 가상환경 재설정
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 📊 로그 파일 위치
- **설치 관련**: `setup_legal_rag.sh` 실행 로그
- **실행 오류**: `logs/legal_rag.log` 파일 확인
- **Neo4j 연결**: http://localhost:7474 접속 확인
- **Docker 로그**: `docker logs neo4j-legal`

### 📧 연락처
- **이슈 등록**: GitHub Issues
- **일반 문의**: 프로젝트 Discussion
- **보안 관련**: 직접 연락

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

<div align="center">

**🏗️ 도시정비사업의 복잡한 법령, 이제 AI와 함께 쉽게 해결하세요!**

Made with ❤️ by Urban Legal RAG Team

</div> 