# app/services/data_service.py
from datetime import datetime
from supabase import Client
from ..supabase_config import get_supabase_client
from postgrest.exceptions import APIError
import json
from uuid import uuid4

supabase: Client = get_supabase_client()

class DataService:
    @staticmethod
    def get_user_by_id(user_id):
        supabase = get_supabase_client()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def create_keyword_analysis(user_id, keyword_id):
        try:
            # First, get the keyword details
            keyword = supabase.table('user_keyword').select('*').eq('id', keyword_id).single().execute()
            print(f"Keyword details: {keyword.data}")

            # Create a new keyword_summary
            new_summary = {
                'user_id': user_id,
                'keyword': keyword.data['keyword'],
                'news_summary': '',  # These will be filled later
                'postive_summary': '',
                'postive_sources_links': '',
                'negative_summary': '',
                'negative_sources_links': '',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            summary_response = supabase.table('keyword_summary').insert(new_summary).execute()
            print(f"Summary insert response: {summary_response}")
            summary_id = summary_response.data[0]['id']

            # Now create the keyword_analysis
            new_analysis = {
                'user_id': user_id,
                'keyword_summary_id': summary_id,
                'created_at': datetime.utcnow().isoformat()
            }
            print(f"Attempting to insert analysis: {new_analysis}")
            analysis_response = supabase.table('keyword_analysis').insert(new_analysis).execute()
            print(f"Analysis insert response: {analysis_response}")
            
            return analysis_response.data[0]['id']
        except Exception as e:
            print(f"Error in create_keyword_analysis: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error args: {e.args}")
            
            if isinstance(e, APIError):
                print(f"API Error details: {e.details}")
                print(f"API Error message: {e.message}")
                print(f"API Error code: {e.code}")
            
            raise

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
        response = supabase.table('analysis_messages').insert(message).execute()
        return response.data[0]
    
    @staticmethod
    def load_conversation(keyword_analysis_id):
        supabase = get_supabase_client()
        response = supabase.table('analysis_messages').select('*').eq('keyword_analysis_id', keyword_analysis_id).order('created_at').execute()
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
        try:
            response = supabase.table('user_keyword').delete().eq('id', keyword_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting keyword: {str(e)}")
            return False
    
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
    
    @staticmethod
    def update_keyword_summary(keyword_id, news_summary, positive_summary, negative_summary, positive_sources_links, negative_sources_links):
        try:
            update_data = {
                'news_summary': news_summary,
                'postive_summary': positive_summary,
                'negative_summary': negative_summary,
                'postive_sources_links': positive_sources_links,
                'negative_sources_links': negative_sources_links,
                'updated_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('keyword_summary').update(update_data).eq('id', keyword_id).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error in update_keyword_summary: {str(e)}")
            return False
    
    @staticmethod
    def update_keyword_summary(analysis_id):
        try:
            # Get the analysis details
            analysis = supabase.table('keyword_analysis').select('*').eq('id', analysis_id).single().execute()
            summary_id = analysis.data['keyword_summary_id']

            # Update the summary (you might want to add more fields here)
            update_data = {
                'last_analyzed_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('keyword_summary').update(update_data).eq('id', summary_id).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error in update_keyword_summary: {str(e)}")
            return False