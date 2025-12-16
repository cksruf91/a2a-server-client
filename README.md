A2A-Server-Client
-----------------

A2A(Agent-to-Agent) 프로토콜 기반 멀티 에이전트 시스템. MCP(Model Context Protocol)를 통해 도메인별 도구를 제공하고, Strands/Google ADK/CrewAI/LangChain 기반
에이전트들이 협업하여 사용자 요청을 처리합니다.

# Project Structure

```
a2a-server-client/
├── app.py                                  # FastAPI web app (port 9999)
├── run_mcp_server.sh                       # MCP 서버 시작 스크립트
├── run_strands_agents.sh                   # Strands 에이전트 시작 스크립트
├── run_google_agents.sh                    # Google ADK 에이전트 시작 스크립트
├── run_crewai_agents.sh                    # CrewAI 에이전트 시작 스크립트
├── run_langchain_agents.sh                 # LangChain 에이전트 시작 스크립트
├── common/                                 # 공통 유틸리티
│   ├── broker.py                           # AgentMessageBroker (A2A 통신)
│   ├── executor.py                         # GenericAgentExecutor
│   ├── http_context.py                     # HTTP 컨텍스트 유틸리티
│   ├── model.py                            # 요청/응답 모델
│   └── types.py                            # 공통 타입 정의
├── strands_agents/                         # Strands 기반 에이전트
│   ├── host_agent.py                       # Host Agent (port 10000)
│   ├── user_agent.py                       # User Agent (port 10003)
│   ├── product_agent.py                    # Product Agent (port 10004)
│   ├── travel_guide_agent.py               # Travel Guide Agent (port 10001)
│   ├── travel_planner_agent.py             # Travel Planner Agent (port 10002)
│   ├── common/
│   │   ├── abstract_agent.py               # Strands 에이전트 기본 클래스
│   │   └── tool.py                         # ToolServerClient (MCP 연동)
│   └── resource/
│       └── prompt.yaml                     # 시스템 프롬프트
├── google_agents/                          # Google ADK 기반 에이전트
│   ├── callback.py                         # 콜백 유틸리티
│   ├── streamlit_app.py                    # Streamlit UI (선택적)
│   ├── common/
│   │   ├── abstract_agent.py               # Google ADK 에이전트 기본 클래스
│   │   ├── remote_agent.py                 # 원격 에이전트 유틸리티
│   │   └── tool.py                         # ToolFilter (태그 기반 도구 필터링)
│   ├── host_agent/
│   │   └── agent.py                        # Host Agent (port 10000)
│   ├── travel_guide_agent/
│   │   └── agent.py                        # Travel Guide Agent (port 10001)
│   └── travel_planner_agent/
│       └── agent.py                        # Travel Planner Agent (port 10002)
├── crew_agents/                            # CrewAI 기반 에이전트
│   ├── common/
│   │   ├── abstract_agent.py               # CrewAI 에이전트 기본 클래스
│   │   └── remote_agent.py                 # 원격 에이전트 유틸리티
│   ├── host_agent/
│   │   └── crew.py                         # Host Agent (port 10000)
│   ├── user_agent/
│   │   └── crew.py                         # User Agent (port 10003)
│   ├── product_agent/
│   │   └── crew.py                         # Product Agent (port 10004)
│   ├── travel_guide_agent/
│   │   └── crew.py                         # Travel Guide Agent (port 10001)
│   └── travel_planner_agent/
│       └── crew.py                         # Travel Planner Agent (port 10002)
├── langchain_agents/                       # LangChain 기반 에이전트
│   ├── common/
│   │   └── abstract_agent.py               # LangChain 에이전트 기본 클래스
│   ├── host_agent.py                       # Host Agent (port 10000)
│   ├── user_agent.py                       # User Agent (port 10003)
│   ├── product_agent.py                    # Product Agent (port 10004)
│   ├── travel_guide_agent.py               # Travel Guide Agent (port 10001)
│   └── travel_planner_agent.py             # Travel Planner Agent (port 10002)
├── mcp/                                    # MCP 서버
│   └── server/
│       ├── user_mcp_server.py              # User MCP Server (port 9011)
│       ├── prod_mcp_server.py              # Product MCP Server (port 9012)
│       └── travel_mcp_server.py            # Travel MCP Server (port 5001)
└── resource/                               # 정적 리소스
    └── app/
        ├── index.html                      # 채팅 UI
        └── app.js                          # 프론트엔드 로직
```

## Architecture

The project consists of four layers:

1. MCP 서버들: 도메인별 도구 제공 (사용자/제품/여행 정보)
2. A2A 에이전트: MCP 도구를 사용하여 특정 도메인을 처리하는 특화된 에이전트
    * Strands 기반 에이전트 (사용자, 제품, 여행_가이드, 여행_플래너)
    * Google ADK 기반 에이전트 (여행 가이드, 플래너, 어시스턴트)
    * CrewAI 기반 에이전트 (사용자, 제품, 여행_가이드, 여행_플래너)
    * LangChain 기반 에이전트 (사용자, 제품, 여행_가이드, 여행_플래너)
3. 호스트 에이전트: A2A 프로토콜을 통해 기본 에이전트들을 조율하는 오케스트레이터 에이전트
4. 웹 애플리케이션 : 호스트 에이전트와 통신하는 채팅 UI가 포함된 FastAPI 앱

# 환경 설정

## Python 버전

- Python 3.12 (`.python-version` 파일에 명시)

## 설치 방법

1. uv 패키지 매니저 설치:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 가상 환경 생성 및 의존성 설치:

```bash
uv sync
```

## 환경 변수

`.env` 파일을 생성(optional)하고 다음 환경 변수를 설정하세요:

```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key  # 또는 GOOGLE_GENAI_API_KEY
```

# MCP server

## 실행 방법

```bash
./run_mcp_server.sh
```

## 서버리스트

| 서버명                | IP        | Port | 역할                    |
|--------------------|-----------|------|-----------------------|
| User MCP Server    | localhost | 9011 | 사용자 정보 제공 도구          |
| Product MCP Server | localhost | 9012 | 제품 정보 제공 도구           |
| Travel MCP Server  | localhost | 5001 | Gemini 기반 여행 정보 제공 도구 |

# Agent server

## GoogleADK

### 실행 방법

```bash
./run_google_agents.sh
```

### 서버 리스트

| 서버명                           | IP        | Port  | 역할                        |
|-------------------------------|-----------|-------|---------------------------|
| Travel Guide Agent            | localhost | 10001 | 관광지 정보 제공 (tag: 'guide')  |
| Travel Planner Agent          | localhost | 10002 | 여행 일정 계획 (tag: 'planner') |
| Travel Assistant Agent (Host) | localhost | 10000 | 여행 전반 지원 (tag: 'travel')  |

## Strands Agents

### 실행 방법

```bash
./run_strands_agents.sh
```

### 서버 리스트

| 서버명                  | IP        | Port  | 역할                    |
|----------------------|-----------|-------|-----------------------|
| Host Agent           | localhost | 10000 | A2A 오케스트레이터 (에이전트 조율) |
| User Agent           | localhost | 10003 | 사용자 정보 처리             |
| Product Agent        | localhost | 10004 | 제품 정보 처리              |
| Travel Guide Agent   | localhost | 10001 | 관광지 정보 제공             |
| Travel Planner Agent | localhost | 10002 | 여행 일정 계획              |

## CrewAi

### 실행 방법

```bash
./run_crewai_agents.sh
```

### 서버 리스트

| 서버명                  | IP        | Port  | 역할                      |
|----------------------|-----------|-------|-------------------------|
| Host Agent           | localhost | 10000 | A2A 오케스트레이터 (CrewAI 기반) |
| User Agent           | localhost | 10003 | 사용자 정보 처리 (CrewAI 기반)   |
| Product Agent        | localhost | 10004 | 제품 정보 처리 (CrewAI 기반)    |
| Travel Guide Agent   | localhost | 10001 | 관광지 정보 제공 (CrewAI 기반)   |
| Travel Planner Agent | localhost | 10002 | 여행 일정 계획 (CrewAI 기반)    |

## LangChain Agents

### 실행 방법

```bash
./run_langchain_agents.sh
```

### 서버 리스트

| 서버명                  | IP        | Port  | 역할                         |
|----------------------|-----------|-------|----------------------------|
| Host Agent           | localhost | 10000 | A2A 오케스트레이터 (LangChain 기반) |
| User Agent           | localhost | 10003 | 사용자 정보 처리 (LangChain 기반)   |
| Product Agent        | localhost | 10004 | 제품 정보 처리 (LangChain 기반)    |
| Travel Guide Agent   | localhost | 10001 | 관광지 정보 제공 (LangChain 기반)   |
| Travel Planner Agent | localhost | 10002 | 여행 일정 계획 (LangChain 기반)    |

# FastAPI

## 실행방법

```bash
uv run uvicorn app:main --reload --host 0.0.0.0 --port 9999
```

Web UI를 제공하는 선택적 레이어로, Host Agent(port 10000)와 통신합니다.

| 서버명             | IP        | Port | 역할                  |
|-----------------|-----------|------|---------------------|
| FastAPI Web App | localhost | 9999 | 채팅 UI 및 REST API 제공 |

# Test UI

Web UI 접속: http://localhost:9999/index

**주의사항**:

- Travel Guide/Planner 에이전트는 포트를 공유하므로, Strands/Google/CrewAI/LangChain 중 하나만 실행해야 합니다.
- 환경 변수 필수: `OPENAI_API_KEY`, `GOOGLE_API_KEY` 또는 `GOOGLE_GENAI_API_KEY`
