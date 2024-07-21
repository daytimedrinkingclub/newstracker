import os
import requests
import json
from typing import Dict, Any

class SearchService:
    BASE_URL = "https://api.tavily.com"
    API_KEY = os.getenv("TAVILY_API_KEY")

    @staticmethod
    def search(query: str, search_depth: str = "advanced", include_images: bool = False, 
               include_answer: bool = True, include_raw_content: bool = False, 
               max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a search using the Tavily Search API.

        Args:
            query (str): The search query string.
            search_depth (str, optional): The depth of the search. Defaults to "basic".
            include_images (bool, optional): Include images in the response. Defaults to False.
            include_answer (bool, optional): Include answers in the search results. Defaults to False.
            include_raw_content (bool, optional): Include raw content in the search results. Defaults to False.
            max_results (int, optional): The maximum number of search results to return. Defaults to 5.

        Returns:
            Dict[str, Any]: The search results.
        """
        endpoint = f"{SearchService.BASE_URL}/search"
        
        payload = {
            "api_key": SearchService.API_KEY,
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
            print(response.json())
            return json.dumps(response.json(), indent=2)
        except requests.RequestException as e:
            print(f"An error occurred while making the request: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Failed to decode the API response")
            return {"error": "Invalid JSON response"}
