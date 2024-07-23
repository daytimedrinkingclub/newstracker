# app/services/agent.py
import os
import logging
import json
import rq
from ..redis_config import get_redis_connection
from typing import Tuple, List, Dict, Any
import anthropic
from datetime import datetime
from ..models.data_service import DataService
from .context import ContextService
from .tool import Tools, ToolsHandler
from flask import current_app

today = datetime.now().strftime("%Y-%m-%d")

class AnthropicChat:
    @staticmethod
    def get_queue():
        return rq.Queue('default', connection=get_redis_connection())
        
    @staticmethod
    def process_conversation(keyword_analysis_id: str, user_id: str) -> Dict[str, Any]:
        with current_app.app_context():
            # Get user plan and API key
            user_plan_type = DataService.get_user_plan_type(user_id)
            keys = DataService.get_user_plan_keys(user_id) if user_plan_type == "free" else os.getenv("ANTHROPIC_API_KEY")
            
            client = anthropic.Anthropic(api_key=keys)
            tools = Tools.load_tools()
            
            # Use ContextService to build the conversation context
            conversation = ContextService.build_context(keyword_analysis_id)
            
            logging.info(f"process_conversation started with {keyword_analysis_id}, context length: {len(conversation)}")
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                temperature=0,
                system=f"""
                Today is {today}.
                Your task is to analyze the news and provide a summary of the news and the sentiment of the news.
                You will be given one keyword or phrase, use all the tools at your disposable to retrieve the news, and then summarize and analyze the news.
                The user will only and only provide the keyword we are not supposed to ask the user anything else, use the tools available for you and always aim to share an update_news_summary.
                """,
                tools=tools,
                messages=conversation,
            )
            
            logging.info(f"Response Received from ANTHROPIC API: {response}")
            
            # Save the assistant's message immediately
            assistant_message = next(block for block in response.content if block.type == "text")
            DataService.save_message(keyword_analysis_id, "assistant", content=assistant_message.text)
            
            if response.stop_reason != "tool_use":
                # No tool use, update status and return
                DataService.update_analysis_status(keyword_analysis_id, "completed")
                return {"status": "completed", "message": "Analysis completed without tool use"}
            
            # Handle tool use
            tool_use = next(block for block in response.content if block.type == "tool_use")
            logging.info(f"Tool use detected: {tool_use.name}")
            
            # Save the tool use information
            DataService.save_message(
                keyword_analysis_id, 
                "assistant", 
                content=assistant_message.text,
                tool_use_id=tool_use.id,
                tool_use_input=json.dumps(tool_use.input),
                tool_name=tool_use.name
            )
            
            # Process the tool use
            tool_result = ToolsHandler.process_tool_use(tool_use.name, tool_use.input, tool_use.id, keyword_analysis_id, user_id)
            
            if tool_use.name == "update_news_summary":
                # Final step: update the summary and complete the analysis
                DataService.update_analysis_status(keyword_analysis_id, "completed")
                # Trigger any necessary notifications or updates here
                return {"status": "completed", "message": "Analysis completed with summary update"}
            
            # For other tools, continue the conversation
            queue = AnthropicChat.get_queue()
            job = queue.enqueue(AnthropicChat.process_conversation, keyword_analysis_id, user_id)
            DataService.update_analysis_status(keyword_analysis_id, "processing", job.id)
            
            return {"status": "processing", "job_id": job.id, "message": "Tool use processed and next job enqueued"}

    @staticmethod
    def handle_chat(user_id: str, keyword: str, keyword_id: str) -> Dict[str, Any]:
        logging.info(f"Starting handle_chat for user_id: {user_id}, keyword: {keyword}, keyword_id: {keyword_id}")
        
        # Save the initial user message (keyword)
        DataService.save_message(keyword_id, "user", content=keyword)
        
        # Create a new keyword analysis entry
        analysis_id = DataService.create_keyword_analysis(user_id, keyword_id)
        
        # Enqueue the first job to start the conversation
        queue = AnthropicChat.get_queue()
        job = queue.enqueue(AnthropicChat.process_conversation, analysis_id, user_id)
        
        # Update the keyword analysis status to "queued"
        DataService.update_analysis_status(analysis_id, "queued", job.id)
        
        logging.info(f"Enqueued job with ID: {job.id}")
        
        return {
            "success": True, 
            "job_id": job.id, 
            "status": "queued", 
            "message": "Analysis task has been queued successfully."
        }