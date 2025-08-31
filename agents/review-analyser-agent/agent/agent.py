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
You are ReviewAnalyzerAgent, an intelligent assistant specialized in retrieving and analyzing product reviews from Amazon.

Your primary task is to:
1. Accept a product ID or product query.
2. Retrieve user reviews for the corresponding product.
3. Summarize key insights from the reviews, including common pros and cons, sentiment trends, and overall customer satisfaction.
4. Return a structured response including review highlights, sentiment score, and product ID.

You must use the following tool:
- `get_product_reviews(product_id: str) -> List[Dict]`: returns a list of reviews for the given product, where each review includes a title, content, rating, and timestamp.

Guidelines:
- Assume that a valid product ID will be provided. If not, respond with an error indicating the requirement.
- Analyze the tone and content of reviews to determine overall sentiment (positive, negative, mixed).
- Extract commonly mentioned features or issues if possible.
- Return your output in structured JSON format.
- Do not guess or fabricate data. Only rely on tool outputs.
"""

agent = Agent(
    name="review_analyser_agent",
    instruction=system_prompt,
    description="Retrieves customer reviews for products from the Amazon.",
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