from fastmcp import Client
import asyncio

async def test_server():
    async with Client("http://localhost:8081/mcp") as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool name: {tool.name}")

if __name__ == "__main__":
    asyncio.run(test_server())