import os
import logging
import json
from ..models.data_service import DataService
from .search import SearchService
from .ai import AnthropicService

class Tools:
    @staticmethod
    def load_tools():
        tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        tools = []
        for file_name in os.listdir(tools_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(tools_dir, file_name)
                try:
                    with open(file_path, "r") as file:
                        tool_data = json.load(file)
                        tools.append(tool_data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error loading tool from {file_path}: {str(e)}")
        logging.info(f"Loaded {len(tools)} tools")
        print(f"Tools: {tools}")
        return tools

class ToolsHandler:
    @staticmethod
    def process_tool_use(tool_name, tool_input, tool_use_id, keyword_analysis_id, user_id):
        logging.info(f"Processing tool use: {tool_name} for analysis {keyword_analysis_id}")
        
        try:
            result = None
            
            if tool_name == "search_web":
                key = DataService.get_user_tavily_keys(user_id)
                result = SearchService.search(tool_input['search_query'], user_id, key=key)
            elif tool_name == "negative_summary":
                result = AnthropicService.call_anthropic("negative_summary", tool_input['data_to_analyse'], user_id)
            elif tool_name == "positive_summary":
                result = AnthropicService.call_anthropic("positive_summary", tool_input['data_to_analyse'], user_id)
            elif tool_name == "update_summary":
                print(f"Tool input of summary: {tool_input}")
                # Fetch the keyword associated with this analysis
                keyword_data = DataService.get_keyword_for_analysis(keyword_analysis_id)
                if not keyword_data:
                    raise ValueError(f"No keyword found for analysis {keyword_analysis_id}")
                
                print(f"Keyword data: {keyword_data}")  # Add this line to print the keyword data
                
                # Add the keyword to the tool_input
                tool_input['keyword'] = keyword_data

                
                
                print(f"Updated tool input: {tool_input}")  # Add this line to print the updated tool input
                
                # Call update_keyword_summary with the updated tool_input
                result = DataService.update_keyword_summary(keyword_analysis_id, user_id, **tool_input)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            if result is None:
                raise ValueError(f"Tool {tool_name} returned None result")

            logging.info(f"Tool {tool_name} executed successfully")

            DataService.save_message(keyword_analysis_id, "user", content="Tool result", tool_use_id=tool_use_id, tool_result=str(result))
            
            return result

        except Exception as e:
            logging.error(f"Error processing tool use for {tool_name}: {str(e)}")
            DataService.update_analysis_status(keyword_analysis_id, "failed", error_message=str(e))
            raise