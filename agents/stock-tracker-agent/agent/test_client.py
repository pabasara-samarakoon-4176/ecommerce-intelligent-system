import os
import traceback
from typing import Any
from uuid import uuid4
import asyncio

from a2a.client import A2AClient
from a2a.types import (
    SendMessageResponse,
    GetTaskResponse,
    SendMessageSuccessResponse,
    Task,
    SendMessageRequest,
    MessageSendParams,
    GetTaskRequest,
    TaskQueryParams,
    SendStreamingMessageRequest,
)
import httpx

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8086")

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


def print_json_response(response: Any, description: str) -> None:
    """Helper function to print the JSON representation of a response."""
    print(f"--- {description} ---")
    if hasattr(response, "root"):
        print(f"{response.root.model_dump_json(exclude_none=True, indent=2)}\n")
    else:
        print(f"{response.model_dump(mode='json', exclude_none=True, indent=2)}\n")


async def run_streaming_test(client: A2AClient) -> None:
    """Tests a single-turn streaming request for a product search."""
    print("--- ⏩ Streaming Product Price Request ---")

    # Send a message to get the price of a specific product using its ASIN.
    price_query = "What is the stock availability of ASIN = B0BTYCRJSS?"
    send_message_payload = create_send_message_payload(text=price_query)
    request = SendStreamingMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    )

    # Stream the response chunks.
    stream_response = client.send_message_streaming(request)
    async for chunk in stream_response:
        print_json_response(chunk, "⏳ Streaming Chunk")


async def main() -> None:
    """Main function to run the tests."""
    print(f"--- 🔄 Connecting to agent at {AGENT_URL}... ---")
    try:
        async with httpx.AsyncClient() as httpx_client:
            client = await A2AClient.get_client_from_agent_card_url(
                httpx_client, AGENT_URL
            )
            print("--- ✅ Connection successful. ---")

            # await run_non_streaming_test(client)
            await run_streaming_test(client)

    except Exception as e:
        traceback.print_exc()
        print(f"--- ❌ An error occurred: {e} ---")
        print("Ensure the agent server is running.")


if __name__ == "__main__":
    asyncio.run(main())