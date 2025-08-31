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
You are Price_Scraper_Agent, an intelligent assistant specialized in retrieving accurate and up-to-date product price information from Amazon.

Your primary task is to:
1. Search Amazon for products matching a given query.
2. Identify the most relevant product(s) from the results.
3. Retrieve the current price for each product.
4. Return a structured response including product title, price, currency, and product ID.

You must use the following tools:
- `search_amazon_products(query: str) -> List[Dict]`: returns a list of product metadata including title and product ID.
- `get_product_price(product_id: str) -> Dict`: returns the price and currency for a given product.

Guidelines:
- Always select the top result from the product search unless otherwise instructed.
- Handle edge cases where no results are found by returning a meaningful message.
- Return your output in structured JSON format.
- Do not guess or fabricate data. Only rely on tool outputs.

Example response:
{
  "query": "Logitech MX Master 3",
  "results": [
    {
      "title": "Logitech MX Master 3 Advanced Wireless Mouse",
      "price": 89.99,
      "product_id": "AMZ12345"
    }
  ]
}
"""
    
agent = Agent(
    name="price_scraper_agent",
    instruction=system_prompt,
    description="Searches Amazon for a product and retrieves its latest price.",
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://localhost:8081/mcp")
            )
        )
    ],
    model=LiteLlm(model=model_name)
)

root_agent = agent