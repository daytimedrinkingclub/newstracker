# app/services/context.py
from ..supabase_config import get_supabase_client

class ContextService:
    @staticmethod
    def build_context(chat_id):
        supabase = get_supabase_client()
        messages = supabase.table('analysis_messages').select('*').eq('keyword_analysis_id', chat_id).order('created_at').execute()
        

        context = []
        for message in messages.data:
            if message['role'] == "user":
                if message.get('tool_result'):
                    context.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message['tool_use_id'],
                                "content": message['tool_result']
                            }
                        ]
                    })
                else:
                    context.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            }
                        ]
                    })
            elif message['role'] == "assistant":
                if message.get('tool_name'):
                    context.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            },
                            {
                                "type": "tool_use",
                                "id": message['tool_use_id'],
                                "name": message['tool_name'],
                                "input": message['tool_input']
                            }
                        ]
                    })
                else:
                    context.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            }
                        ]
                    })

        return context