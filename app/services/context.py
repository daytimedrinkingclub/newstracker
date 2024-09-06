# app/services/context.py
import uuid
from ..supabase_config import get_supabase_client

class ContextService:
    @staticmethod
    def build_context(chat_id):
        supabase = get_supabase_client()
        messages = supabase.table('analysis_messages').select('*').eq('keyword_analysis_id', chat_id).order('created_at').execute()
        
        context = []
        last_role = None

        for message in messages.data:
            current_role = message['role']
            
            # Skip if this message has the same role as the previous one
            if current_role == last_role:
                continue

            if current_role == "user":
                content = [{"type": "text", "text": message['content']}]
                if message.get('tool_result'):
                    content.append({
                        "type": "tool_result",
                        "tool_use_id": message['tool_use_id'],
                        "content": message['tool_result']
                    })
            elif current_role == "assistant":
                content = [{"type": "text", "text": message['content']}]
                if message.get('tool_name'):
                    content.append({
                        "type": "tool_use",
                        "id": message['tool_use_id'] or str(uuid.uuid4()),
                        "name": message['tool_name'],
                        "input": message['tool_input']
                    })
            else:
                continue  # Skip unknown roles

            context.append({"role": current_role, "content": content})
            last_role = current_role

        return context