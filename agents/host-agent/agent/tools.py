import asyncio
import os
from dotenv import load_dotenv
from typing import Dict
from remote_connections import RemoteConnections

load_dotenv()
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

async def delegate_task(agent_name: str, task_description: str) -> str:
    """Delegates a task to a specified child agent via A2A protocol.

    Args:
        agent_name: The logical name of the target agent (e.g., 'notion_agent').
        task_description: A detailed description of the task for the child agent to perform.

    Returns:
        The result from the child agent, or an error message.
    """
    if agent_name not in AGENT_URL_MAP:
        return f"Error: Agent '{agent_name}' is not a known agent. Available agents are: {list(AGENT_URL_MAP.keys())}"

    agent_url = AGENT_URL_MAP[agent_name]
    remote_connections = await RemoteConnections.create(
        timeout=60.0
    )  # Increased timeout for complex tasks

    try:
        # The task_description is passed directly as the query to the child agent.
        # This allows the host agent to give rich, detailed instructions.
        result = await remote_connections.invoke_agent(agent_url, task_description)

        if isinstance(result, dict):
            if result.get("error"):
                return f"Error from {agent_name}: {result['error']}"
            elif result.get("result"):
                return result["result"]
            else:
                return f"Error: Unexpected response format from {agent_name}"
        else:
            return "Error: Invalid response format from RemoteConnections"

    except Exception as e:
        return f"Error delegating task to {agent_name}: {str(e)}"
    finally:
        await remote_connections.close()


def delegate_task_sync(agent_name: str, task_description: str) -> str:
    """
    Synchronous wrapper for delegate_task to be used as an ADK tool.

    This function handles running the async 'delegate_task' function from
    a synchronous context, which is required for ADK tools. It intelligently
    handles cases where an asyncio event loop is already running.

    Args:
        agent_name: The logical name of the target agent.
        task_description: A detailed description of the task.

    Returns:
        The result from the child agent, or an error message.
    """
    try:
        # This pattern handles both scenarios: running within an existing
        # event loop (like in some web frameworks or notebooks) or running
        # in a standard synchronous environment.
        try:
            asyncio.get_running_loop()
            # If inside an event loop, run the async code in a separate thread
            # to avoid "RuntimeError: cannot be called from a running event loop".
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, delegate_task(agent_name, task_description)
                )
                return future.result(
                    timeout=90
                )  # Generous timeout for orchestrated tasks
        except RuntimeError:
            # No running event loop, so we can safely use asyncio.run()
            return asyncio.run(delegate_task(agent_name, task_description))
    except Exception as e:
        return f"Error in sync delegation wrapper: {str(e)}"