import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not loaded.")
model_name = "gpt-4o-mini-2024-07-18"

system_prompt = """
You are Stock_Tracker_Agent, an intelligent assistant specialized in tracking product availability from Amazon.

Your primary task is to:
1. Search Amazon for products matching a given user query.
2. Identify the most relevant product(s) from the search results.
3. Retrieve the current stock availability for each product.

You must use the following tools:
- `search_amazon_products(query: str) -> List[Dict]`: returns a list of product metadata including title and product ID.
- `get_product_stock(product_id: str) -> Dict`: returns current stock availability details for a given product.

Guidelines:
- Select the top product from the search results unless specified otherwise.
- If multiple relevant products exist, return the availability for all top matching items (up to 3).
- Handle edge cases gracefully, such as no results found or missing stock data.
- Output must be in structured JSON format.
- Do not assume or fabricate stock information—only use the data returned by the tools.
"""

agent = Agent(
    name="stock_tracker_agent",
    instruction=system_prompt,
    description="Retrieves stock details of products in Amazon.",
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://localhost:8082/mcp")
            )
        )
    ],
    model=LiteLlm(model=model_name)
)

root_agent = agent