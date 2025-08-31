import asyncio
from fastmcp import Client

async def test_server():
    async with Client("http://localhost:8083/mcp") as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool found: {tool.name}")
        print(">>> Calling stock tracker:")
        result = await client.call_tool("get_product_stock", {"product_id": "B09SWW583J"})
        print(f">>> Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_server())