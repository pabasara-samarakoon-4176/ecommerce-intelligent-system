from fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os
from typing import Dict, List

load_dotenv()
rapid_api_key = os.getenv('RAPID_API_KEY')
if not rapid_api_key:
    ValueError("RAPID_API_KEY is not found.")
port = os.getenv('PORT', 8082)
if not port:
    ValueError("PORT is not found.")

mcp = FastMCP("review-analyser", host="0.0.0.0", port=port)

@mcp.tool()
def get_product_reviews(product_id: str) -> List[Dict]:
    """
    Fetches reviews for a given Amazon product using the RapidAPI Amazon Data Scraper.

    Args:
        product_id (str): The ASIN (Amazon Standard Identification Number) of the product.

    Returns:
        List[Dict]: A list of dictionaries, each containing review details such as
            'asin', 'title', 'rating', and 'content'.
    """
    url = "https://amazon-data-scraper-api3.p.rapidapi.com/queries"
    payload = {
        "source": "amazon_product",
        "query": product_id,
        "geo_location": "90210",
        "parse": True
    }
    headers = {
        "x-rapidapi-key": "59b2bf441emsh3d2d32af0263a80p195f9cjsn7b69606cc48f",
        "x-rapidapi-host": "amazon-data-scraper-api3.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    reviews = []
    try:
        reviews_list = (
            data.get("results", [{}])[0]
            .get("content", {})
            .get("reviews", [])
        )
        for review in reviews_list:
            reviews.append({
                "asin": product_id,
                "title": review.get("title"),
                "rating": review.get("rating"),
                "content": review.get("content")
            })
    except Exception:
        pass
    return reviews

if __name__ == "__main__":
    mcp.run(transport="streamable-http")