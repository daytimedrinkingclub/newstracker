import os
import re
import json
from ..models.data_service import DataService
from .search import SearchService
from .ai import AnthropicService

# This class is called by the Toolhandler function
class Tools:
    @staticmethod
    def load_tools():
        tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        tools = []
        for file_name in os.listdir(tools_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(tools_dir, file_name)
                with open(file_path, "r") as file:
                    tool_data = json.load(file)
                    tools.append(tool_data)
        print(f"Tools loaded and returned {len(tools)} tools")
        print(f"Loaded tools \n\n --------------------{tools} \n\n -----------")
        return tools
    
    @staticmethod
    def write_to_file(file_content, file_name):
        # Ensure the file has a .txt extension
        if not file_name.endswith('.txt'):
            file_name += '.txt'
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Current directory: {current_dir}")
        # Create the full file path
        file_path = os.path.join(current_dir, file_name)
        print(f"File created at path: {file_path}")
        # Create and write to the text file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_content)
        
        return f"File '{file_name}' has been created in the current directory and the content has been written successfully."

# This class can be called to process the tool use and call the required tool and return the tool result
class ToolsHandler:
    @staticmethod
    def process_tool_use(tool_name, tool_input, tool_use_id, chat_id):
        print(f"process_tool_use function called")
        if tool_name == "search_web":
            result = SearchService.search(tool_input["query"])
            DataService.save_message(chat_id, "user", content=result, tool_use_id=tool_use_id, tool_result=result)
            return result
        elif tool_name in ["positive_research", "negative_research"]:
            user_message = f"{tool_input['query']}"
            result = AnthropicService.call_anthropic(tool_name, user_message)
            DataService.save_message(chat_id, "user", content=result, tool_use_id=tool_use_id, tool_result=result)
            return result
        elif tool_name == "update_news_summary":
            keyword_id = tool_input.get('keyword_id')
            news_summary = tool_input.get('news_summary')
            positive_summary = tool_input.get('positive_summary')
            negative_summary = tool_input.get('negative_summary')
            positive_sources_links = tool_input.get('positive_sources_links', [])
            negative_sources_links = tool_input.get('negative_sources_links', [])
            
            DataService.update_keyword_summary(
                keyword_id,
                news_summary,
                positive_summary,
                negative_summary,
                positive_sources_links,
                negative_sources_links
            )
            
            DataService.save_message(chat_id, "system", content="Keyword summary updated", tool_use_id=tool_use_id)
            return None
        else:
            return "Error: Invalid tool name"