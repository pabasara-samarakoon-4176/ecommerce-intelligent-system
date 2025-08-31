from fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os
from typing import Dict

load_dotenv()
rapid_api_key = os.getenv('RAPID_API_KEY')
if not rapid_api_key:
    ValueError("RAPID_API_KEY is not found.")
port = os.getenv('PORT', 8083)
if not port:
    ValueError("PORT is not found.")

mcp = FastMCP("price-scraper", host="0.0.0.0", port=port)

@mcp.tool()
def get_product_stock(product_id: str) -> Dict:
    """
    Fetches stock information for a given Amazon product ID (ASIN).

    Args:
        product_id (str): The Amazon product ASIN to query.

    Returns:
        Dict: A dictionary containing the ASIN, product title, and stock status.
              Returns None if the information cannot be retrieved or parsed.
    """
    url = "https://amazon-data-scraper-api3.p.rapidapi.com/queries"
    payload = {
        "source": "amazon_product",
        "query": product_id,
        "geo_location": "90210",
        "parse": True
    }
    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "amazon-data-scraper-api3.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    try:
        product_info = data.get("results", [{}])[0].get("content", {})
        title = product_info.get('title')
        stock = product_info.get("stock")  
        return {
            'asin': product_id,
            'title': title,
            'stock': stock
        }
    except Exception:
        return None
    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")