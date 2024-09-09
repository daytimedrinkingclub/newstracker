import logging
import requests
import json
from typing import Dict, Any
from ..models.data_service import DataService
from ..utils.rate_limiter import RateLimiter, exponential_backoff

class SearchService:
    @staticmethod
    @RateLimiter(max_calls=5, period=60)  # 5 calls per minute
    @exponential_backoff(max_retries=3, base_delay=2)
    def search(query: str, user_id: str, search_depth: str = "advanced", include_images: bool = False, 
               include_answer: bool = True, include_raw_content: bool = False, 
               max_results: int = 5, key: str = None) -> Dict[str, Any]:
        """
        Perform a search using the Tavily Search API.

        Args:
            query (str): The search query string.
            user_id (str): The user ID for the search.
            search_depth (str, optional): The depth of the search. Defaults to "advanced".
            include_images (bool, optional): Include images in the response. Defaults to False.
            include_answer (bool, optional): Include answers in the search results. Defaults to True.
            include_raw_content (bool, optional): Include raw content in the search results. Defaults to False.
            max_results (int, optional): The maximum number of search results to return. Defaults to 5.
            key (str, optional): The API key for Tavily. Defaults to None.

        Returns:
            Dict[str, Any]: The search results.
        """
        BASE_URL = "https://api.tavily.com"
        endpoint = f"{BASE_URL}/search"
        
        payload = {
            "api_key": key,
            "query": query,
            "search_depth": search_depth,
            "include_images": include_images,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results
        }

        try:
            logging.info("seeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            logging.info(f"Sending request to Tavily API with payload: {payload}")
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            logging.info(f"Search result length: {len(str(result))} characters")
            logging.info(f"Search result: {result}")
            return result
        except requests.RequestException as e:
            if e.response is not None and e.response.status_code == 422:
                logging.error(f"Received a 422 error. Response content: {e.response.content}")
                return {"error": "Invalid request parameters. Please check your input."}
            logging.error(f"An error occurred while making the request: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Failed to decode the API response")
            return {"error": "Invalid JSON response"}
