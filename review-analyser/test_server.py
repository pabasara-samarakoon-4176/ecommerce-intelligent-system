import asyncio
from fastmcp import Client

async def test_server():
    async with Client("http://localhost:8082/mcp") as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool found: {tool.name}")
        print(">>> Calling review analyser:")
        result = await client.call_tool("get_product_reviews", {"product_id": "B09SWW583J"})
        print(f">>> Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_server())