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
from collections import defaultdict

today = datetime.now().strftime("%Y-%m-%d")

class AnthropicChat:
    @staticmethod
    def process_conversation(keyword_analysis_id: str, user_id: str) -> Dict[str, Any]:
        from .tool import ToolsHandler
        with current_app.app_context():
            try:
                keyword = DataService.get_keyword_for_analysis(keyword_analysis_id)
                if not keyword:
                    raise ValueError("No keyword found for this analysis")

                print(f"Processing conversation for keyword: {keyword}")

                user_plan_type = DataService.get_user_plans(user_id)
                keys = DataService.get_user_anthropic_keys(user_id) if user_plan_type == "free" else os.getenv("ANTHROPIC_API_KEY")
                
                client = anthropic.Anthropic(api_key=keys)
                tools = Tools.load_tools()
                print(f"Loaded {len(tools)} tools")
                
                context = ContextService.build_context(keyword_analysis_id)
                print(f"newnew Built context with {len(context)} messages")

                # Ensure the first message is always about the keyword
                if not context or 'Analyze the news for the keyword:' not in context[0]['content'][0]['text']:
                    context.insert(0, {
                        "role": "user", 
                        "content": [{"type": "text", "text": f"Analyze the news for the keyword: {keyword}"}]
                    })
                    DataService.save_message(keyword_analysis_id, "user", content=f"Analyze the news for the keyword: {keyword}")

                system = f"""
                 Today is {today}.
                    Your task is to analyze the news and provide a summary of the news and the sentiment of the news.
                    You will be given one keyword or phrase, use all the tools at your disposal to retrieve the news, and then summarize and analyze the news.
                    The user will only provide the keyword; we are not supposed to ask the user anything else. Use the tools available for you and always aim to share an update_news_summary.
                    """

                # logging.info(f"Sending request to Anthropic API for keyword: {keyword}")
                # logging.info(f"Request payload: model={client}, temperature={0}, system={system}, tools={tools}, messages={context}")

                print(f"Full context structure: {json.dumps(context, indent=2)}")

                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    temperature=0,
                    system=system,
                    tools=tools,
                    messages=context,
                )

                print(f"Responseeee content: {response}")

                print(f"Received response from Anthropic API for keyword: {keyword}")
                print(f"Response content: {response.content}")

                assistant_message = next(block for block in response.content if block.type == "text")
                DataService.save_message(keyword_analysis_id, "assistant", content=assistant_message.text)

                tool_use = next((block for block in response.content if block.type == "tool_use"), None)
                if tool_use:
                    print(f"Tool use detected: {tool_use.name}")
                    print(f"Tool input: {tool_use.input}")  # Add this line to print the tool input
                    
                    DataService.save_message(
                        keyword_analysis_id, 
                        "assistant", 
                        content=assistant_message.text,
                        tool_use_id=tool_use.id,
                        tool_use_input=tool_use.input,
                        tool_name=tool_use.name
                    )
                    print(f"Tool name: {tool_use.name}")
                    print(f"Tool input: {tool_use.input}")
                    print(f"Tool use id: {tool_use.id}")
                    print(f"Keyword analysis id: {keyword_analysis_id}")
                    print(f"User id: {user_id}")
                    # Process tool use directly
                    result = ToolsHandler.process_tool_use(
                        tool_name=tool_use.name,  # Pass the tool name correctly
                        tool_input=tool_use.input,  # Pass the tool input correctly
                        tool_use_id=tool_use.id,
                        keyword_analysis_id=keyword_analysis_id,
                        user_id=user_id
                    )
                    print(f"Tool result: {result}")  # Add this line to print the tool result
                    DataService.update_analysis_status(keyword_analysis_id, "processing")
                    return AnthropicChat.process_conversation(keyword_analysis_id, user_id)
                else:
                    print("No tool use detected in the response")
                    DataService.save_message(
                        keyword_analysis_id, 
                        "assistant", 
                        content=assistant_message.text
                    )
                    DataService.update_analysis_status(keyword_analysis_id, "completed")
                    return {"status": "completed", "message": "Analysis completed successfully"}

            except Exception as e:
                logging.error(f"Error in process_conversation: {str(e)}")
                DataService.update_analysis_status(keyword_analysis_id, "failed", error_message=str(e))
                raise

    @staticmethod
    def handle_chat(user_id: str, keyword_id: str, analysis_id: str, keyword: str) -> Dict[str, Any]:
        print(f"Starting analysis for keyword: {keyword}")
        try:
            DataService.save_message(analysis_id, "user", content=f"Analyze the news for the keyword: {keyword}")
            result = AnthropicChat.process_conversation(analysis_id, user_id)
            return result
        except Exception as e:
            logging.error(f"Error in handle_chat: {str(e)}")
            DataService.update_analysis_status(analysis_id, "failed", error_message=str(e))
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to start analysis: {str(e)}"
            }