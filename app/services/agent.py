import os
import json
from typing import Tuple, List, Dict, Any
import anthropic
from datetime import datetime
from ..models.data_service import DataService
from .context import ContextService
from .tool import Tools, ToolsHandler

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
today = datetime.now().strftime("%Y-%m-%d")

def parse_response_content(content: str) -> Tuple[str, str, str, List[str], List[str]]:
    # Implement logic to parse the content and extract the required information
    # This is a placeholder implementation
    news_summary = content
    positive_summary = ""
    negative_summary = ""
    positive_sources = []
    negative_sources = []
    return news_summary, positive_summary, negative_summary, positive_sources, negative_sources


class AnthropicChat:
    @staticmethod
    def process_conversation(keyword_analysis_id: str) -> anthropic.types.Message:
        tools = Tools.load_tools()
        conversation = ContextService.build_context(keyword_analysis_id)
        print(f"process_conversation started with {keyword_analysis_id} with current context_len: {len(conversation)}")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0,
            system=f"""
            Today is {today}.
            Your task is to analyze the news and provide a summary of the news and the sentiment of the news.
            You will be given one keyword or phrase, use all the tools at your disposable to retrieve the news, and then summarize and analyze the news.
            """,
            tools=tools,
            messages=conversation,
        )
        print(f"Response Received from ANTHROPIC API: {response}")

        if response.stop_reason != "tool_use":
            # No tool use, return the final response
            print(f"No tool use, returning assistant response which needs a user message")
            DataService.save_message(keyword_analysis_id, "assistant", content=response.content[0].text)
            return response

        # Handle tool use
        print(f"Tool use detected, processing tool use")
        tool_use = next(block for block in response.content if block.type == "tool_use")

        print(f"Tool Name: {tool_use.name}")
        
        DataService.save_message(keyword_analysis_id, "assistant", content=response.content[0].text, tool_use_id=tool_use.id, tool_use_input=tool_use.input, tool_name=tool_use.name)

        tool_result = ToolsHandler.process_tool_use(tool_use.name, tool_use.input, tool_use.id, keyword_analysis_id)

        print(f"Tool Result received: {tool_result}")

        if tool_result:
            # If a tool result is received, build the latest context and call process_conversation again
            return AnthropicChat.process_conversation(keyword_analysis_id)

        return response

    @staticmethod
    def handle_chat(keyword_analysis_id: str, keyword: str, anthropic_api_key: str) -> Dict[str, Any]:
        try:
            print(f"Starting handle_chat for keyword_analysis_id: {keyword_analysis_id}, keyword: {keyword}")
            
            save_result = DataService.save_message(keyword_analysis_id, "user", content=keyword)
            print(f"Saved initial user message: {save_result}")
            
            response = AnthropicChat.process_conversation(keyword_analysis_id)
            print(f"process_conversation response: {response}")
            
            # Check if the analysis is complete
            if response.stop_reason != "tool_use":
                print("Analysis complete, parsing response")
                content = response.content[0].text
                news_summary, positive_summary, negative_summary, positive_sources, negative_sources = parse_response_content(content)
                
                return {
                    'status': 'completed',
                    'news_summary': news_summary,
                    'positive_summary': positive_summary,
                    'negative_summary': negative_summary,
                    'positive_sources_links': positive_sources,
                    'negative_sources_links': negative_sources
                }
            else:
                print("Analysis in progress, tool use detected")
                return {'status': 'in_progress'}
        except Exception as e:
            print(f"Error in handle_chat: {str(e)}")
            return {'status': 'failed'}
        
