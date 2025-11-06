import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities, TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.agents import SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

AGENT_URLS = [
    'http://localhost:9101',
    'http://localhost:9102'
]
REMOTE_AGENTS: list[RemoteA2aAgent] = [
    RemoteA2aAgent(
        name="user_agent",
        description="this agent can control and access user information like name, address, etc..",
        agent_card=f"http://localhost:9101{AGENT_CARD_WELL_KNOWN_PATH}",
    ),
    RemoteA2aAgent(
        name="product_agent",
        description="this agent can control and access product information like name, price, description etc..",
        agent_card=f"http://localhost:9102{AGENT_CARD_WELL_KNOWN_PATH}",
    )
]

if __name__ == "__main__":
    host_agent = SequentialAgent(
        name='ChatHostAgent',
        sub_agents=REMOTE_AGENTS,
    )

    host_agent_card = AgentCard(
        name=host_agent.name,
        url='http://localhost:10022',
        description='Orchestrates Agent',
        version='1.0',
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=['text/plain'],
        default_output_modes=['application/json'],
        preferred_transport=TransportProtocol.jsonrpc,
        skills=[
            AgentSkill(
                id='Host Agent Skill',
                name='Host Agent Skill',
                description='Orchestrates Agent for user',
                tags=['main'],
                examples=[
                    "hi",
                    "tell me product name of id \'PDO1234\'",
                ],
            )
        ],
    )

    runner = Runner(
        app_name=host_agent.name,
        agent=host_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=config)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    server = A2AStarletteApplication(
        agent_card=host_agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9200)
