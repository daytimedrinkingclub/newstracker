# app/services/data_service.py
from ..supabase_config import get_supabase_client
from postgrest.exceptions import APIError
import json
from uuid import uuid4

class DataService:
    @staticmethod
    def get_user_by_id(user_id):
        supabase = get_supabase_client()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def create_keyword_analysis(user_id, keyword_summary_id):
        supabase = get_supabase_client()
        new_keyword_analysis_id = str(uuid4())
        new_keyword_analysis = {
            'id': new_keyword_analysis_id,
            'user_id': user_id,
            'keyword_summary_id': keyword_summary_id
        }
        response = supabase.table('keyword_analyses').insert(new_keyword_analysis).execute()
        print(f"New Keyword Analysis created with ID: {new_keyword_analysis_id}")
        return new_keyword_analysis_id

    @staticmethod
    def save_message(keyword_analysis_id, role, content, tool_use_id=None, tool_use_input=None, tool_name=None, tool_result=None):
        supabase = get_supabase_client()
        message = {
            'keyword_analysis_id': keyword_analysis_id,
            'role': role,
            'content': content,
            'tool_name': tool_name,
            'tool_use_id': tool_use_id,
            'tool_input': tool_use_input,
            'tool_result': tool_result
        }
        response = supabase.table('messages').insert(message).execute()
        return response.data[0]
    
    @staticmethod
    def load_conversation(keyword_analysis_id):
        supabase = get_supabase_client()
        response = supabase.table('messages').select('*').eq('keyword_analysis_id', keyword_analysis_id).order('created_at').execute()
        messages = response.data
        conversation = []
        for message in messages:
            if message['role'] == "user":
                if message['tool_result']:
                    conversation.append({
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
                    conversation.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            }
                        ]
                    })
            elif message['role'] == "assistant":
                if message['tool_name']:
                    conversation.append({
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
                    conversation.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": message['content']
                            }
                        ]
                    })
        return conversation
    
    @staticmethod
    def get_user_plans(user_id):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_plan').select('*').eq('user_id', user_id).execute()
            return response.data
        except APIError as e:
            print(f"Error fetching user plans: {str(e)}")
            return []
    
    @staticmethod
    def get_news_feed(user_id):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_keyword').select('*').eq('user_id', user_id).execute()
            user_keywords = response.data

            for keyword in user_keywords:
                keyword['refresh_button'] = True  # Add a refresh button for each keyword
            print(user_keywords)
            return user_keywords
        except APIError as e:
            print(f"Error fetching user keywords: {str(e)}")
            return []
    @staticmethod
    def add_user_plan(user_id, plan):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_plan').insert({
                'user_id': user_id,
                'plan': plan
            }).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            print(f"Error adding user plan: {str(e)}")
            return None

    @staticmethod
    def update_user_plan(plan_id, new_plan):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_plan').update({
                'plan': new_plan
            }).eq('id', plan_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            print(f"Error updating user plan: {str(e)}")
            return None
        
    @staticmethod
    def delete_user_plan(plan_id):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_plan').delete().eq('id', plan_id).execute()
            return True
        except APIError as e:
            print(f"Error deleting user plan: {str(e)}")
            return False
        
    @staticmethod
    def update_user_api_tokens(user_id, anthropic_api_key, tavily_api_key):
        supabase = get_supabase_client()
        try:
            # Check if a record already exists for this user
            existing_record = supabase.table('user_api_token').select('*').eq('user_id', user_id).execute()
            
            if existing_record.data:
                # Update existing record
                response = supabase.table('user_api_token').update({
                    'anthropic_api_key': anthropic_api_key,
                    'tavily_api_key': tavily_api_key
                }).eq('user_id', user_id).execute()
            else:
                # Insert new record
                response = supabase.table('user_api_token').insert({
                    'user_id': user_id,
                    'anthropic_api_key': anthropic_api_key,
                    'tavily_api_key': tavily_api_key
                }).execute()
            
            return response.data[0] if response.data else None
        except APIError as e:
            print(f"Error updating user API tokens: {str(e)}")
            return None
        
    @staticmethod
    def delete_user_api_tokens(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_api_token').delete().eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_user_keywords(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').select('*').eq('user_id', user_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def add_user_keyword(user_id, keyword):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').insert({
            'user_id': user_id,
            'keyword': keyword
        }).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete_user_keyword(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').delete().eq('id', keyword_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update_user_keyword(keyword_id, new_keyword):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').update({
            'keyword': new_keyword
        }).eq('id', keyword_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_news_details(user_id, keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_summary').select('*').eq('id', keyword_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_keyword_by_id(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').select('*').eq('id', keyword_id).execute()
        return response.data[0] if response.data else None
    

    @staticmethod
    def get_keyword_analysis_details(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_summary').select('*').eq('id', keyword_id).execute()
        if response.data:
            summary = response.data[0]
            return {
                'keyword': summary['keyword'],
                'news_summary': summary['news_summary'],
                'positive_summary': summary['postive_summary'],
                'positive_sources_links': summary['postive_sources_links'],
                'negative_summary': summary['negative_summary'],
                'negative_sources_links': summary['negative_sources_links'],
                'created_at': summary['created_at'],
                'updated_at': summary['updated_at']
            }
        return None