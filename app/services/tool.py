import os
import logging
import re
import json
from rq import get_current_job
from ..utils.redis_task_manager import enqueue_task
from ..models.data_service import DataService
from .search import SearchService
from .ai import AnthropicService

# This class is called by the Toolhandler function
class Tools:
    # This function loads the tools from the tools folder and returns the tools
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
        logging.info(f"Tools loaded and returned {len(tools)} tools")
        logging.info(f"Loaded tools \n\n --------------------{tools} \n\n -----------")
        return tools
    
# This class can be called to process the tool use and call the required tool and return the tool result
class ToolsHandler:
    @staticmethod
    def process_tool_use(tool_name, tool_input, tool_use_id, chat_id, user_id):
        logging.info(f"process_tool_use function called")
        result = None
        
        if tool_name == "search_web":
            result = SearchService.search(tool_input["query"], user_id)
            DataService.save_message(chat_id, "user", content=result, tool_use_id=tool_use_id, tool_result=result)
            # enque the next job where we return the message to handle chat function
        elif tool_name in ["positive_research", "negative_research"]:
            user_message = f"{tool_input['query']}"
            result = AnthropicService.call_anthropic(tool_name, user_message, user_id)
            DataService.save_message(chat_id, "user", content=result, tool_use_id=tool_use_id, tool_result=result)
            # enque the next job where we return the message to handle chat function
        # if tool name is update summary we need to end the ai simulation save the last message and update the keyword_summary table in supabase
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
            
            result = "Keyword summary updated"
        else:
            result = "Error: Invalid tool name"
        
        if result:
            DataService.save_message(chat_id, "assistant", content=result, tool_use_id=tool_use_id, tool_result=result)
        logging.info(f"process_tool_use function returned {result}")
        return "analysis_complete and keyword analysis summary updated"