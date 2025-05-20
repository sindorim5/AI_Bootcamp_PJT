# AI_Bootcamp_PJT


---


## 프로젝트 페이지

[Notion](https://www.notion.so/sindorim5/AI-Bootcamp-1f9d58e5754a8051a9a7cd96c353adcb?pvs=4)

---

## 개요

**AI 금융 상담사**는 사용자의 투자 성향,자본금,관심 주제(예: “반도체”, “장기투자”)를 입력받아

Multi-Agent(Market Data -> Retriever -> Analysis -> Portfolio) 파이프라인으로

실시간 시세, 뉴스 데이터를 수집,분석하고 맞춤형 포트폴리오와 리포트를 제공하는 Streamlit 애플리케이션입니다.

## 주요 기능

| 기능                   | 설명                                                                    |
| ---------------------- | ----------------------------------------------------------------------- |
| **Multi-Agent**        | LangGraph 기반 5단계 에이전트가 CoT 프롬프트로 협업해 리포트를 작성     |
| **실시간 시세 반영**   | yfinance API로 주가·지수 데이터를 수집하여 포트폴리오 리스크 계산       |
| **RAG 기반 정보 검색** | DuckDuckGo + FAISS 벡터스토어로 최신 뉴스·리포트를 실시간 검색          |
| **대화형 UI**          | Streamlit UI + 세션별 DB 저장/조회                                      |
| **로컬 DB**            | SQLAlchemy + SQLite                                                     |
| **Langfuse 연동**      | `LANGFUSE_PUBLIC/SECRET_KEY` 입력 시 프롬프트·토큰 사용량 모니터링 지원 |

---

## 프로젝트 구조

```
app/
├── main.py          # Streamlit 진입점
├── controller/      # UI·대화 흐름 제어
├── view/            # Streamlit 컴포넌트
├── workflow/        # LangGraph 그래프 & 에이전트
│   └── agent/       # 개별 에이전트 정의
├── retrieval/       # RAG-검색 쿼리·문서 수집 로직
├── database/        # SQLAlchemy 모델·Seed·Repository
├── common/          # 설정·유틸리티 함수
└── .env             # 환경 변수
```

---


## 프로젝트 실행

1. .env 설정 (아래는 .env 설정 예시)

   > ```
   > AOAI_ENDPOINT=https://.....openai.azure.com/
   > AOAI_API_KEY=5kW....
   > AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
   > AOAI_DEPLOY_GPT4O=gpt-4o
   > AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large
   > AOAI_DEPLOY_EMBED_3_SMALL=text-embedding-3-small
   > AOAI_DEPLOY_EMBED_ADA=text-embedding-ada-002
   > AOAI_API_VERSION="2024-02-01"
   > LANGFUSE_PUBLIC_KEY=pk....
   > LANGFUSE_SECRET_KEY=sk....
   > LANGFUSE_HOST=https://cloud.langfuse.com
   > DB_PATH="finance_agent.db"
   > DB_TYPE="SQLITE_DB"
   > ```

2. python package 설치

   > ```
   > pip3 install -r requirements.txt
   > ```

3. streamlit 실행

   > ```
   > steamlit run main.py
   > ```

# AI_Bootcamp_PJT

- [Notion](https://www.notion.so/sindorim5/AI-Bootcamp-1f9d58e5754a8051a9a7cd96c353adcb?pvs=4)

---

## 개요

**AI 금융 상담사**는 사용자의 투자 성향,자본금,관심 주제(예: “반도체”, “장기투자”)를 입력받아

Multi-Agent(Market Data -> Retriever -> Analysis -> Portfolio) 파이프라인으로

실시간 시세, 뉴스 데이터를 수집,분석하고 맞춤형 포트폴리오와 리포트를 제공하는 Streamlit 애플리케이션입니다.

## 주요 기능

| 기능                   | 설명                                                                    |
| ---------------------- | ----------------------------------------------------------------------- |
| **Multi-Agent**        | LangGraph 기반 5단계 에이전트가 CoT 프롬프트로 협업해 리포트를 작성     |
| **실시간 시세 반영**   | yfinance API로 주가·지수 데이터를 수집하여 포트폴리오 리스크 계산       |
| **RAG 기반 정보 검색** | DuckDuckGo + FAISS 벡터스토어로 최신 뉴스·리포트를 실시간 검색          |
| **대화형 UI**          | Streamlit UI + 세션별 DB 저장/조회                                      |
| **로컬 DB**            | SQLAlchemy + SQLite                                                     |
| **Langfuse 연동**      | `LANGFUSE_PUBLIC/SECRET_KEY` 입력 시 프롬프트·토큰 사용량 모니터링 지원 |

---

## 프로젝트 구조

```
app/
├── main.py          # Streamlit 진입점
├── controller/      # UI·대화 흐름 제어
├── view/            # Streamlit 컴포넌트
├── workflow/        # LangGraph 그래프 & 에이전트
│   └── agent/       # 개별 에이전트 정의
├── retrieval/       # RAG-검색 쿼리·문서 수집 로직
├── database/        # SQLAlchemy 모델·Seed·Repository
├── common/          # 설정·유틸리티 함수
└── .env             # 환경 변수
```

---

## 프로젝트 실행

1. .env 설정 (아래는 .env 설정 예시)

## 프로젝트 실행

1. .env 설정 (아래는 .env 설정 예시)

   > ```
   > AOAI_ENDPOINT=https://.....openai.azure.com/
   > AOAI_API_KEY=5kW....
   > AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
   > AOAI_DEPLOY_GPT4O=gpt-4o
   > AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large
   > AOAI_DEPLOY_EMBED_3_SMALL=text-embedding-3-small
   > AOAI_DEPLOY_EMBED_ADA=text-embedding-ada-002
   > AOAI_API_VERSION="2024-02-01"
   > LANGFUSE_PUBLIC_KEY=pk....
   > LANGFUSE_SECRET_KEY=sk....
   > LANGFUSE_HOST=https://cloud.langfuse.com
   > DB_PATH="finance_agent.db"
   > DB_TYPE="SQLITE_DB"
   > ```

2. python package 설치

   > ```
   > pip3 install -r requirements.txt
   > ```

3. streamlit 실행

   > ```
   > steamlit run main.py
   > ```
