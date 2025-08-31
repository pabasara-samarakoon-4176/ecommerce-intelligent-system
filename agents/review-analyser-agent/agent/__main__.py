import logging
import os

import click
from dotenv import load_dotenv
import uvicorn

from agent import root_agent
from agent_executor import ADKAgentExecutor

from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

logger = logging.getLogger(__name__)

load_dotenv(".env")
GOOGLE_GENAI_USE_VERTEXAI = os.getenv('GOOGLE_GENAI_USE_VERTEXAI')
if not GOOGLE_GENAI_USE_VERTEXAI:
    raise ValueError("GOOGLE_GENAI_USE_VERTEXAI is not loaded.")

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not loaded.")

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host: str, port: int):
    if GOOGLE_GENAI_USE_VERTEXAI != "TRUE" and not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set and "
            "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
        )
    
    review_skill = AgentSkill(
        id="get_product_reviews",
        name="Get product reviews",
        description="Can get the reviews of a product given the ASIN",
        tags=["Get Amazon reviews"],
        examples=["What are the reviews of product ASIN = B0CRXK7WVM?"]
    )

    agent_card = AgentCard(
        name="Review Analyser Agent",
        description="Can get product reviews from Amazon",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[review_skill],
    )

    runner = Runner(
        app_name=agent_card.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = ADKAgentExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AFastAPIApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()