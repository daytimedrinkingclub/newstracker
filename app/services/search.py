import requests
import json
from typing import Dict, Any
from ..models.data_service import DataService

class SearchService:
    @staticmethod
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
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if e.response is not None and e.response.status_code == 422:
                print("Received a 422 error. Please check your request parameters.")
                return {"error": "Invalid request parameters. Please check your input."}
            print(f"An error occurred while making the request: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Failed to decode the API response")
            return {"error": "Invalid JSON response"}
