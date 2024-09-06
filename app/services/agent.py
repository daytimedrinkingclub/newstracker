import os
import json
import logging
import anthropic
from datetime import datetime
from ..models.data_service import DataService
from .context import ContextService
from .tool import Tools
from typing import List, Dict, Any
from flask import current_app

today = datetime.now().strftime("%Y-%m-%d")

class AnthropicChat:
    @staticmethod
    def process_conversation(keyword_analysis_id: str, user_id: str) -> Dict[str, Any]:
        from .tool import ToolsHandler  # Move this import inside the method
        with current_app.app_context():
            try:
                # Get user plan and API key
                user_plan_type = DataService.get_user_plans(user_id)
                logging.info(f"User plan type: {user_plan_type}")
                keys = DataService.get_user_anthropic_keys(user_id) if user_plan_type == "free" else os.getenv("ANTHROPIC_API_KEY")
                logging.info(f"API keys retrieved: {'Yes' if keys else 'No'}")
                
                client = anthropic.Anthropic(api_key=keys)
                tools = Tools.load_tools()
                logging.info(f"Number of tools loaded: {len(tools)}")
                
                if not tools:
                    raise ValueError("No tools were loaded. Check your tool JSON files.")
                
                conversation = ContextService.build_context(keyword_analysis_id)
                
                # Validate conversation structure
                for i, message in enumerate(conversation):
                    if message['role'] == 'user' and any(block['type'] == 'tool_result' for block in message['content']):
                        if i == 0 or not any(block['type'] == 'tool_use' for block in conversation[i-1]['content']):
                            # Remove invalid tool_result block
                            message['content'] = [block for block in message['content'] if block['type'] != 'tool_result']
                
                logging.info(f"Conversation context length: {len(conversation)}")
                logging.info(f"Sending request to Anthropic API")
                
                logging.info(f"Conversation context: {json.dumps(conversation, indent=2)}")
                logging.info(f"Number of messages in conversation: {len(conversation)}")
                
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=2000,
                    temperature=0,
                    system=f"""
                    Today is {today}.
                    Your task is to analyze the news and provide a summary of the news and the sentiment of the news.
                    You will be given one keyword or phrase, use all the tools at your disposal to retrieve the news, and then summarize and analyze the news.
                    The user will only provide the keyword; we are not supposed to ask the user anything else. Use the tools available for you and always aim to share an update_news_summary.
                    """,
                    tools=tools,
                    messages=conversation,
                )
                logging.info(f"Response Received from ANTHROPIC API: {response}")
                
                assistant_message = next(block for block in response.content if block.type == "text")
                DataService.save_message(keyword_analysis_id, "assistant", content=assistant_message.text)

                if response.stop_reason != "tool_use":
                    # No tool use, update status and return
                    DataService.update_analysis_status(keyword_analysis_id, "need_user_input")
                    return {"status": "need_user_input", "message": "Need further user input to continue the analysis"}

                # Handle tool use
                tool_use = next(block for block in response.content if block.type == "tool_use")
                logging.info(f"Tool use detected: {tool_use.name}")
                
                DataService.save_message(
                    keyword_analysis_id, 
                    "assistant", 
                    content=assistant_message.text,
                    tool_use_id=tool_use.id,
                    tool_use_input=tool_use.input,
                    tool_name=tool_use.name
                )

                # Process tool use directly
                result = ToolsHandler.process_tool_use(tool_use.name, tool_use.input, tool_use.id, keyword_analysis_id, user_id)
                DataService.update_analysis_status(keyword_analysis_id, "processing")

                return {"status": "processing", "message": "Tool use processed and continuing analysis"}

            except Exception as e:
                logging.error(f"Error in process_conversation: {str(e)}")
                DataService.update_analysis_status(keyword_analysis_id, "failed", error_message=str(e))
                raise

    @staticmethod
    def handle_chat(user_id: str, keyword_id: str, analysis_id: str) -> Dict[str, Any]:
        logging.info(f"Starting handle_chat for user_id: {user_id}, keyword_id: {keyword_id}, analysis_id: {analysis_id}")
        try:
            keyword = DataService.get_keyword_by_id(keyword_id)
            DataService.save_message(analysis_id, "user", content=keyword)
            result = AnthropicChat.process_conversation(analysis_id, user_id)
            DataService.update_analysis_status(analysis_id, result['status'])
            logging.info(f"Analysis started for {analysis_id}")
            return result
        except Exception as e:
            logging.error(f"Error in handle_chat: {str(e)}")
            DataService.update_analysis_status(analysis_id, "failed", error_message=str(e))
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to start analysis: {str(e)}"
            }