from fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os
from typing import Dict, List

load_dotenv()
rapid_api_key = os.getenv('RAPID_API_KEY')
if not rapid_api_key:
    ValueError("RAPID_API_KEY is not found.")
port = os.getenv('PORT', 8081)
if not port:
    ValueError("PORT is not found.")

mcp = FastMCP("price-scraper", host="0.0.0.0", port=port)

@mcp.tool()
def get_product_price(product_id: str) -> Dict:
    """
    Fetches the price and title of a product from Amazon using its ASIN.

    Args:
        product_id (str): The ASIN of the product.

    Returns:
        dict: Dictionary containing 'asin', 'title', and 'price' if found, else None.
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
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        product_info = data.get("results", [{}])[0].get("content", {})
        title = product_info.get("title")
        price = product_info.get("price")
        if title is not None and price is not None:
            return {
                'asin': product_id,
                'title': title,
                'price': price
            }
        else:
            return None
    except Exception:
        return None

@mcp.tool()
def search_amazon_products(query: str) -> List[Dict]:
    """
    Searches Amazon for products matching the query string.

    Args:
        query (str): The search term.

    Returns:
        list: List of dictionaries, each containing 'asin', 'title', 'price', 'url', and 'image'.
    """
    url = "https://amazon-data-scraper-api3.p.rapidapi.com/queries"
    payload = {
        "source": "amazon_search",
        "query": query,
        "geo_location": "60607",
        "domain": "com",
        "parse": True
    }
    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "amazon-data-scraper-api3.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    results = []
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        organic_products = (
            data.get("results", [{}])[0]
            .get("content", {})
            .get("results", {})
            .get("organic", [])
        )
        for item in organic_products:
            results.append({
                "asin": item.get("asin"),
                "title": item.get("title"),
                "price": item.get("price"),
                "url": "https://www.amazon.com" + item.get("url", ""),
                "image": item.get("url_image")
            })
        return results
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

if __name__ == "__main__":
    mcp.run(transport="streamable-http")