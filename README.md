a2a-server-client
-----------------

A2A(Agent-to-Agent) 프로토콜 기반 멀티 에이전트 시스템. MCP(Model Context Protocol)를 통해 도메인별 도구를 제공하고, Strands/Google ADK/CrewAI 기반 에이전트들이 협업하여 사용자 요청을 처리합니다.

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

| 서버명                | IP        | Port   | 역할                    |
|--------------------|-----------|--------|-----------------------|
| User MCP Server    | localhost | 9011   | 사용자 정보 제공 도구          |
| Product MCP Server | localhost | 9012   | 제품 정보 제공 도구           |
| Travel MCP Server  | localhost | 5001   | Gemini 기반 여행 정보 제공 도구 |

# Agent server

## GoogleADK

### 실행 방법

```bash
./run_google_agents.sh
```

### 서버 리스트

| 서버명                           | IP        | Port   | 역할                        |
|-------------------------------|-----------|--------|---------------------------|
| Travel Guide Agent            | localhost | 10001  | 관광지 정보 제공 (tag: 'guide')  |
| Travel Planner Agent          | localhost | 10002  | 여행 일정 계획 (tag: 'planner') |
| Travel Assistant Agent (Host) | localhost | 10000  | 여행 전반 지원 (tag: 'travel')  |

## Strands Agents

### 실행 방법

```bash
./run_strands_agents.sh
```

### 서버 리스트

| 서버명                  | IP        | Port   | 역할                    |
|----------------------|-----------|--------|-----------------------|
| Host Agent           | localhost | 10000  | A2A 오케스트레이터 (에이전트 조율) |
| User Agent           | localhost | 10003  | 사용자 정보 처리             |
| Product Agent        | localhost | 10004  | 제품 정보 처리              |
| Travel Guide Agent   | localhost | 10001  | 관광지 정보 제공             |
| Travel Planner Agent | localhost | 10002  | 여행 일정 계획              |

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

# FastAPI

## 실행방법

```bash
uv run uvicorn app:main --reload --host 0.0.0.0 --port 9999
```

Web UI를 제공하는 선택적 레이어로, Host Agent(port 10000)와 통신합니다.

| 서버명             | IP        | Port  | 역할                  |
|-----------------|-----------|-------|---------------------|
| FastAPI Web App | localhost | 9999  | 채팅 UI 및 REST API 제공 |

# Test UI

Web UI 접속: http://localhost:9999/index 

**주의사항**:
- Travel Guide/Planner 에이전트는 포트를 공유하므로, Strands/Google/CrewAI 중 하나만 실행해야 합니다.
- 환경 변수 필수: `OPENAI_API_KEY`, `GOOGLE_API_KEY` 또는 `GOOGLE_GENAI_API_KEY`
