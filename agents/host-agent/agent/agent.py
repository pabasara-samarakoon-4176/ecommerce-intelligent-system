import asyncio
import logging
from typing import Any, Dict, Optional
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import os
# from tools import delegate_task_sync

from a2a.client import A2AClient, A2ACardResolver
from uuid import uuid4
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.agents.llm_agent import LlmAgent
import httpx
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendStreamingMessageRequest
)

logger = logging.getLogger(__name__)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not loaded.")
model_name = "gpt-4o-mini-2024-07-18"

PRICE_A2A_SERVER_URL = os.getenv('PRICE_A2A_SERVER_URL')
if not PRICE_A2A_SERVER_URL:
    raise ValueError("PRICE_A2A_SERVER_URL is not loaded.")
REVIEW_A2A_SERVER_URL = os.getenv('REVIEW_A2A_SERVER_URL')
if not REVIEW_A2A_SERVER_URL:
    raise ValueError("REVIEW_A2A_SERVER_URL is not loaded.")
STOCK_A2A_SERVER_URL = os.getenv('STOCK_A2A_SERVER_URL')
if not STOCK_A2A_SERVER_URL:
    raise ValueError("STOCK_A2A_SERVER_URL is not loaded.")

AGENT_URL_MAP: Dict[str, str] = {
    "price_scraper_agent": PRICE_A2A_SERVER_URL,
    "review_analyser_agent": REVIEW_A2A_SERVER_URL,
    "stock_tracker_agent": STOCK_A2A_SERVER_URL
}

async def list_agents() -> list[AgentCard]:
    """
    Fetch all AgentCard metadata from the registry,
    return as a list of plain dicts.
    """
    cards_data = []

    async with httpx.AsyncClient() as httpx_client:
        for agent_name, base_url in AGENT_URL_MAP.items():
            logger.info(f"Initializing A2ACardResolver for {agent_name} at {base_url}.")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=base_url,
            )

            try:
                logger.info(
                    f"Attempting to fetch public agent card from: {base_url}"
                )
                public_card = await resolver.get_agent_card()
                logger.info("Successfully fetched public agent card:")
                logger.info(
                    public_card.model_dump_json(indent=2, exclude_none=True)
                )
                print(f"Fetched agent '{public_card.name}' from registry at {base_url}")
                cards_data.append(public_card)

            except Exception as e:
                logger.error(
                    f"Critical error fetching public agent card from {base_url}: {e}",
                    exc_info=True  
                )
                continue
        
        return cards_data
    
def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
    """Helper function to create the payload for sending a message."""
    payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }

    if task_id:
        payload["message"]["taskId"] = task_id

    if context_id:
        payload["message"]["contextId"] = context_id
    return payload

def print_json_response(response: Any) -> None:
    """Helper function to print the JSON representation of a response."""
    if hasattr(response, "root"):
        print(f"{response.root.model_dump_json(exclude_none=True, indent=2)}\n")
    else:
        print(f"{response.model_dump(mode='json', exclude_none=True, indent=2)}\n")

def get_text_from_json_response(response: Any) -> str:
    """
    Extracts and returns the text content from a JSON response object.
    """
    try:
        if hasattr(response, "model_dump"):
            response = response.model_dump()
        
        text_content = response.get('result', {}).get('artifact', {}).get('parts', [{}])[0].get('text', '')
        if text_content.startswith('```json'):
            text_content = text_content.strip('`').strip('json').strip('\n`').strip()

        return text_content
        
    except (TypeError, KeyError, IndexError) as e:
        print(f"Error extracting text from response: {e}")
        return ""
    
async def call_agent(agent_name: str, message: str):
    """
    Given an agent_name string and a user message,
    find that agent's URL, send the task, and return its reply.
    """
    cards = await list_agents()
    target_card: Optional[AgentCard] = None

    for card in cards:
        if card.name == agent_name:
            target_card = card
            break
    
    if not target_card:
        logger.error(f"Agent '{agent_name}' not found.")
        return

    logger.info(f"✅ Found agent '{target_card.name}'. Connecting to {target_card.url}")

    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=target_card
        )
        print(f"Connected to A2AClient at: {target_card.url}")
        send_message_payload = create_send_message_payload(text=message)
        request = SendStreamingMessageRequest(
            id=str(uuid4()), params=send_message_payload
        )
        response_stream = []
        try:
            async for chunk in client.send_message_streaming(request):
                if chunk:
                    response_stream.append(chunk)
            return response_stream[-2]
        except Exception as e:
            logger.error(f"Error while calling agent '{agent_name}': {e}", exc_info=True)
            return "No response"

async def main():
    agent_name = "Price Scraper Agent"
    query = "Check for the price of 'wireless headphones' in Amazon."
    
    print(f"--- Calling agent '{agent_name}' with query: '{query}' ---")
    response = await call_agent(agent_name, query)
    print(f"--- ✅ Response from {agent_name}: ---")
    print(get_text_from_json_response(response))

if __name__ == "__main__":
    asyncio.run(main())

system_prompt = """
You are the **Host Agent**, a master orchestrator for a team of specialized
child agents. Your primary purpose is to receive user requests, understand user's
ultimate goal, and delegate the necessary tasks to the appropriate child agent to 
fulfill the request.

## Your Core Directives

1.  **Remember and Reason**: Before acting, review the entire conversation history. The user's previous messages and your prior actions are your primary source of context. Use this context to understand the user's intent, even if it's implied across several turns.
2.  **Deconstruct and Delegate**: Your main job is to use the `delegate_task_sync` tool. Analyze the user's request, informed by the conversation history, and formulate a clear, detailed `task_description` for the appropriate child agent.
3.  **Act as an Orchestrator, Not a Doer**: You do not perform tasks like searching or converting text to speech yourself. You delegate these tasks to the experts. Your intelligence lies in choosing the right agent and giving it the right instructions.
4.  **Synthesize and Respond**: After a child agent completes a task, you will receive its report. Synthesize this information into a helpful, user-friendly response. Do not just dump the raw output.
5.  **Multi-Step Workflows**: For complex requests that require multiple agents (e.g., "find this in Notion and read it to me"), you must chain your delegations. First, delegate the search task to `notion_agent`. Once you have the result, delegate the text-to-speech task to `elevenlabs_agent`.

## Your Team: The Child Agent Roster

You have the following agents at your disposal. You must use their `agent_name` when calling the `delegate_task_sync` tool.

### 1. `price_scraper_agent`
-   **Capabilities**: Can search Amazon for products and get their prices.
-   **When to use**: If the user wants search and identify prices for certain products in Amazon.
-   **Example `task_description`**:
    -   `"The user want to learn prices of `wireless headphones` in Amazon."`
    -   `"The user wants to learn average price of `wireless headphones` in Amazon."`

### 2. `review_analyser_agent`
-   **Capabilities**: Retrieves customer reviews for a given Amazon product, analyzes them to identify common pros and cons, determines overall sentiment, and summarizes customer feedback trends.
-   **When to use**: When the task involves understanding customer opinions, product quality feedback, or extracting sentiment insights from Amazon product reviews.
-   **Example `task_description`**:
    -  "Analyze reviews for the Logitech MX Master 3 and summarize key pros and cons."
    -  "Find the sentiment for customer reviews of the Kindle Paperwhite."

### 3. `stock_tracker_agent`
-   **Capabilities**: Searches Amazon for a product and retrieves its current stock availability, including whether it is in stock, out of stock, or low in stock.
-   **When to use**: When the task requires checking whether a product is available for purchase or monitoring inventory status.
-   **Example `task_description`**:
    -  "Check if the Sony WH-1000XM5 headphones are currently in stock."
    -  "Find the stock status for the Apple MacBook Air M2."

## Your Only Tool: `delegate_task_sync`

```python
delegate_task_sync(agent_name: str, task_description: str) -> str
```

-   `agent_name` (required): The name of the agent from the roster (`price_scraper_agent`, `review_analyser_agent` or `stock_tracker_agent`).
-   `task_description` (required): A clear, comprehensive, and standalone instruction for the child agent. While you have access to the full conversation history, the child agents do not. Therefore, you **must** provide all necessary context from our conversation in this description.
"""

# agent = Agent(
#     name="host_agent_orchestrator",
#     description="A master orchestrator that delegates tasks to specialized child agents (price_scraper_agent, review_analyser_agent, stock_tracker_agent) using a generic A2A communication tool.",
#     instruction=system_prompt,
#     tools=[delegate_task_sync],
#     model=LiteLlm(model=model_name)
# )

# root_agent = agent