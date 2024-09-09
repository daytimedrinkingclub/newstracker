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
        logging.info(f"Tools loaded and returned {len(tools)} tools")
        if not tools:
            logging.warning("No tools were loaded. Check your tool JSON files.")
        return tools

class ToolsHandler:
    @staticmethod
    def process_tool_use(tool_name, tool_input, tool_use_id, keyword_analysis_id, user_id):
        from .agent import AnthropicChat
        logging.info(f"Processing tool use: {tool_name} for analysis {keyword_analysis_id}")
        
        try:
            result = None
            if tool_name == "search_web":
                key = DataService.get_user_tavily_keys(user_id)
                logging.info(f"Search query: {tool_input['search_query']}")
                logging.info(f"User ID: {user_id}")
                logging.info(f"Tavily API key: {key}")
                result = SearchService.search(tool_input['search_query'], user_id, key=key)
                logging.info(f"Search results: {result}")
                
                # Truncate the result if it's too long
                max_result_length = 4000  # Adjust this value as needed
                if len(str(result)) > max_result_length:
                    logging.warning(f"Search result truncated from {len(str(result))} to {max_result_length} characters")
                    result = str(result)[:max_result_length] + "... (truncated)"
            
            elif tool_name == "positive_summary":
                result = AnthropicService.call_anthropic(tool_input['data_to_analyse'], "positive_prompt", user_id)
            elif tool_name == "negative_summary":
                result = AnthropicService.call_anthropic(tool_input['data_to_analyse'], "negative_prompt", user_id)
            elif tool_name == "update_summary":
                result = DataService.update_keyword_summary(keyword_analysis_id, **tool_input)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            if result is None:
                raise ValueError(f"Tool {tool_name} returned None result")

            logging.info(f"Tool {tool_name} executed successfully")

            # Save the tool result
            DataService.save_message(keyword_analysis_id, "user", content="Tool result", tool_use_id=tool_use_id, tool_result=str(result))
            
            # Continue the conversation
            AnthropicChat.process_conversation(keyword_analysis_id, user_id)

            logging.info(f"Continued conversation for analysis {keyword_analysis_id}")

            return result

        except Exception as e:
            logging.error(f"Error processing tool use for {tool_name}: {str(e)}")
            DataService.update_analysis_status(keyword_analysis_id, "failed", error_message=str(e))
            raise