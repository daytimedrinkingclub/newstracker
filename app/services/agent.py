# app/services/agent.py
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
from ..utils.rabbitmq_task_manager import enqueue_task

today = datetime.now().strftime("%Y-%m-%d")

class AnthropicChat:
    @staticmethod
    def process_conversation(keyword_analysis_id: str, user_id: str) -> Dict[str, Any]:
        from .tool import ToolsHandler  # Move this import inside the method
        with current_app.app_context():
            try:
                # Get user plan and API key
                user_plan_type = DataService.get_user_plans(user_id)
                keys = DataService.get_user_anthropic_keys(user_id) if user_plan_type == "free" else os.getenv("ANTHROPIC_API_KEY")
                
                client = anthropic.Anthropic(api_key=keys)
                tools = Tools.load_tools()
                
                if not tools:
                    raise ValueError("No tools were loaded. Check your tool JSON files.")
                
                conversation = ContextService.build_context(keyword_analysis_id)
                logging.info(f"process_conversation started with {keyword_analysis_id}, context length: {len(conversation)}")
                
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

                # Enqueue tool use processing as a background task
                job = enqueue_task(ToolsHandler.process_tool_use, tool_use.name, tool_use.input, tool_use.id, keyword_analysis_id, user_id)
                DataService.update_analysis_status(keyword_analysis_id, "processing_tool_call", job)


                return {"status": "processing", "message": "Tool use processed and next job enqueued"}

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
            job = enqueue_task(AnthropicChat.process_conversation, args=(analysis_id, user_id))
            DataService.update_analysis_status(analysis_id, "queued", job)
            logging.info(f"Enqueued job for analysis {analysis_id}")
            return {
                "success": True, 
                "status": "queued", 
                "message": "Analysis task has been queued successfully."
            }
        except Exception as e:
            logging.error(f"Error in handle_chat: {str(e)}")
            DataService.update_analysis_status(analysis_id, "failed", error_message=str(e))
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to start analysis: {str(e)}"
            }