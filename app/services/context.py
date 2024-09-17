# app/services/context.py
import json
from ..supabase_config import get_supabase_client
import logging

class ContextService:
    @staticmethod
    def build_context(chat_id):
        supabase = get_supabase_client()
        messages = supabase.table('analysis_messages').select('*').eq('keyword_analysis_id', chat_id).order('created_at').execute()
        
        context = []
        current_assistant_message = None
        last_tool_use_id = None

        for message in messages.data:
            if message['role'] == "user":
                if current_assistant_message:
                    context.append(current_assistant_message)
                    print("newnew context update (assistant):", json.dumps(current_assistant_message, indent=2))
                    current_assistant_message = None
                
                if message.get('tool_result') and last_tool_use_id:
                    new_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": last_tool_use_id,
                                "content": message['tool_result']
                            }
                        ]
                    }
                    context.append(new_message)
                    print("newnew context update (tool result):", json.dumps(new_message, indent=2))
                    last_tool_use_id = None
                else:
                    new_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            }
                        ]
                    }
                    context.append(new_message)
                    print("newnew context update (user):", json.dumps(new_message, indent=2))
            elif message['role'] == "assistant":
                if not current_assistant_message:
                    current_assistant_message = {
                        "role": "assistant",
                        "content": []
                    }
                
                if not any(content['type'] == 'text' and content['text'] == message['content'] 
                           for content in current_assistant_message['content']):
                    current_assistant_message["content"].append({
                        "type": "text",
                        "text": message['content']
                    })
                
                if message.get('tool_name'):
                    current_assistant_message["content"].append({
                        "type": "tool_use",
                        "id": message['tool_use_id'],
                        "name": message['tool_name'],
                        "input": json.loads(message['tool_input'])
                    })
                    last_tool_use_id = message['tool_use_id']

        if current_assistant_message:
            context.append(current_assistant_message)
            print("newnew context update (final assistant):", json.dumps(current_assistant_message, indent=2))

        print(f"newnew full context for chat_id {chat_id}:", json.dumps(context, indent=2))
        return context