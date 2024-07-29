# app/services/data_service.py
import os
import uuid
import logging
from datetime import datetime
from supabase import Client
from ..supabase_config import get_supabase_client
from postgrest.exceptions import APIError
import json
from uuid import uuid4

supabase: Client = get_supabase_client()

class DataService:
    @staticmethod
    # function to get user data by sending user_id
    def get_user_by_id(user_id):
        supabase = get_supabase_client()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def get_user_keyword_count(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').select('id', count='exact').eq('user_id', user_id).execute()
        return response.count

    @staticmethod
    def get_user_keyword_limit(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_plan').select('keyword_limit').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]['keyword_limit']
        return None  # Return None for unlimited (freemium)
    
    # function to save message to the database in the analysis_messages table
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
        logging.info(f"Attempting to save message: {message}")
        try:
            response = supabase.table('analysis_messages').insert(message).execute()
            logging.info(f"Message saved successfully: {response.data[0]}")
            return response.data[0]
        except Exception as e:
            logging.error(f"Error saving message: {str(e)}")
            return None
    
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
            logging.info(f"User plans fetched successfully: {response.data}")
            return response.data
        except APIError as e:
            print(f"Error fetching user plans: {str(e)}")
            return []
    
    @staticmethod
    def get_news_feed(user_id):
        supabase = get_supabase_client()
        try:
            # Fetch user keywords
            keyword_response = supabase.table('user_keyword').select('*').eq('user_id', user_id).execute()
            user_keywords = keyword_response.data

            for keyword in user_keywords:
                keyword['refresh_button'] = True  # Add a refresh button for each keyword

                # Fetch the latest keyword analysis for the current keyword
                analysis_response = supabase.table('keyword_analysis').select('status, updated_at').eq('keyword_id', keyword['id']).order('created_at', desc=True).limit(1).execute()
                if analysis_response.data:
                    keyword['last_analysis'] = datetime.fromisoformat(analysis_response.data[0]['updated_at'])
                else:
                    keyword['last_analysis'] = None

                # Fetch the keyword summary for the current keyword
                summary_response = supabase.table('keyword_summary').select('news_summary').eq('id', keyword['id']).execute()
                if summary_response.data:
                    keyword['news_summary'] = summary_response.data[0]['news_summary']
                else:
                    keyword['news_summary'] = None

            logging.info(f"User keywords fetched successfully: {user_keywords}")
            return user_keywords
        except APIError as e:
            logging.error(f"Error fetching user keywords: {str(e)}")
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
            logging.error(f"Error adding user plan: {str(e)}")
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
            logging.error(f"Error updating user plan: {str(e)}")
            return None
        
    @staticmethod
    def delete_user_plan(plan_id):
        supabase = get_supabase_client()
        try:
            response = supabase.table('user_plan').delete().eq('id', plan_id).execute()
            return True
        except APIError as e:
            logging.error(f"Error deleting user plan: {str(e)}")
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
            logging.error(f"Error updating user API tokens: {str(e)}")
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
        try:
            # Check the user's keyword limit
            keyword_limit = DataService.get_user_keyword_limit(user_id)
            if keyword_limit is not None:
                current_count = DataService.get_user_keyword_count(user_id)
                if current_count >= keyword_limit:
                    raise Exception("Keyword limit reached. Upgrade your plan to add more keywords.")

            # Insert the user keyword
            keyword_response = supabase.table('user_keyword').insert({
                'user_id': user_id,
                'keyword': keyword
            }).execute()
            
            if not keyword_response.data:
                raise Exception("Failed to insert user keyword")
            
            keyword_id = keyword_response.data[0]['id']
            
            # Insert the keyword summary
            summary_response = supabase.table('keyword_summary').insert({
                'user_id': user_id,
                'keyword_id': keyword_id,
                'keyword': keyword,
                'news_summary': '',
                'postive_summary': '',
                'postive_sources_links': '',
                'negative_summary': '',
                'negative_sources_links': ''
            }).execute()
            
            if not summary_response.data:
                raise Exception("Failed to insert keyword summary")
            
            summary_id = summary_response.data[0]['id']
            
            # Insert the keyword analysis
            analysis_response = supabase.table('keyword_analysis').insert({
                'user_id': user_id,
                'keyword_id': keyword_id,
                'keyword_summary_id': summary_id,
                'status': 'pending'
            }).execute()
            
            if not analysis_response.data:
                raise Exception("Failed to insert keyword analysis")
            
            logging.info(f"Successfully added keyword {keyword} for user {user_id}")
            return keyword_response.data[0]
        except Exception as e:
            logging.error(f"Error adding user keyword: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller
    
    @staticmethod
    def delete_user_keyword(keyword_id):
        supabase = get_supabase_client()
        try:
            # First, get all related keyword_analysis ids
            keyword_analysis_response = supabase.table('keyword_analysis').select('id').eq('keyword_id', keyword_id).execute()
            keyword_analysis_ids = [item['id'] for item in keyword_analysis_response.data]

            # Delete related analysis messages
            if keyword_analysis_ids:
                analysis_messages_response = supabase.table('analysis_messages').delete().in_('keyword_analysis_id', keyword_analysis_ids).execute()
                logging.info(f"Deleted {len(analysis_messages_response.data)} analysis messages")
            else:
                logging.info("No related analysis messages to delete")

            # Delete related keyword analysis
            keyword_analysis_delete_response = supabase.table('keyword_analysis').delete().eq('keyword_id', keyword_id).execute()
            logging.info(f"Deleted {len(keyword_analysis_delete_response.data)} keyword analysis entries")

            # Delete related keyword summary
            keyword_summary_response = supabase.table('keyword_summary').delete().eq('keyword_id', keyword_id).execute()
            logging.info(f"Deleted {len(keyword_summary_response.data)} keyword summary entries")

            # Finally, delete the user keyword
            user_keyword_response = supabase.table('user_keyword').delete().eq('id', keyword_id).execute()
            logging.info(f"Deleted {len(user_keyword_response.data)} user keyword entries")

            # Check if any deletions were successful
            if (len(keyword_analysis_ids) > 0 or
                len(keyword_summary_response.data) > 0 or
                len(keyword_analysis_delete_response.data) > 0 or
                len(user_keyword_response.data) > 0):
                return True
            else:
                logging.warning(f"No data found to delete for keyword_id: {keyword_id}")
                return False

        except Exception as e:
            logging.error(f"Error deleting keyword and related data: {str(e)}")
            return False
        
    @staticmethod
    def update_keyword_summary(analysis_id, user_id, news_summary, positive_summary, negative_summary, positive_sources_links, negative_sources_links):
        try:
            # Get the analysis details
            analysis = supabase.table('keyword_analysis').select('*').eq('id', analysis_id).single().execute()
            id = analysis.data['keyword_summary_id']
            keyword_id = analysis.data['keyword_id']
            keyword = analysis.data['keyword']

            update_data = {
                'id': id,
                'user_id': user_id,
                'keyword_id': keyword_id,
                'keyword': keyword,
                'news_summary': news_summary,
                'postive_summary': positive_summary,
                'negative_summary': negative_summary,
                'postive_sources_links': positive_sources_links,
                'negative_sources_links': negative_sources_links,
                'updated_at': datetime.utcnow().isoformat()
            }
            response = supabase.table('keyword_summary').update(update_data).eq('id', id).eq('keyword_id', keyword_id).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error in update_keyword_summary: {str(e)}")
            return False
    
    @staticmethod       
    def get_news_details(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_summary').select('*').eq('id', keyword_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_keyword_by_id(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('user_keyword').select('keyword').eq('id', keyword_id).execute()
        return response.data[0]['keyword'] if response.data else None
    
    @staticmethod
    def get_keyword_analysis_details(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_summary').select('*, keyword_analysis(status, job_id)').eq('keyword_id', keyword_id).execute()
        if response.data:
            summary = response.data[0]
            analysis = summary['keyword_analysis'][0] if summary['keyword_analysis'] else {}
            return {
                'id': summary['id'],
                'user_id': summary['user_id'],
                'keyword_id': summary['keyword_id'],
                'keyword': summary['keyword'],
                'news_summary': summary['news_summary'],
                'positive_summary': summary['postive_summary'],
                'positive_sources_links': summary['postive_sources_links'].split(',') if summary['postive_sources_links'] else [],
                'negative_summary': summary['negative_summary'],
                'negative_sources_links': summary['negative_sources_links'].split(',') if summary['negative_sources_links'] else [],
                'created_at': summary['created_at'],
                'updated_at': summary['updated_at'],
                'analysis_status': analysis.get('status', 'pending'),
                'analysis_job_id': analysis.get('job_id')
            }
        return None

    @staticmethod
    def update_analysis_status(analysis_id, status, job_id=None, error_message=None):
        supabase = get_supabase_client()
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat(),
                'job_id': job_id
            }
            if error_message:
                update_data['error_message'] = error_message
            response = supabase.table('keyword_analysis').update(update_data).eq('id', analysis_id).execute()
            return bool(response.data)
        except Exception as e:
            logging.error(f"Error updating analysis status: {str(e)}")
            return False
        
    @staticmethod
    def get_analysis_by_job_id(job_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_analysis').select('*').eq('job_id', job_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_active_analysis_for_keyword(keyword_id):
        supabase = get_supabase_client()
        try:
            response = supabase.table('keyword_analysis').select('*').eq('keyword_id', keyword_id).in_('status', ['pending', 'processing']).order('created_at', desc=True).limit(1).execute()
            logging.info(f"Active analysis query result: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error checking for active analysis: {str(e)}")
            return None
        
    @staticmethod
    def get_user_anthropic_keys(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_api_token').select('anthropic_api_key').eq('user_id', user_id).execute()
        if response.data and response.data[0]['anthropic_api_key']:
            return response.data[0]['anthropic_api_key']
        else:
            raise ValueError("Anthropic API key not found or empty for the user")

    @staticmethod
    def get_user_tavily_keys(user_id):
        supabase = get_supabase_client()
        response = supabase.table('user_api_token').select('tavily_api_key').eq('user_id', user_id).execute()
        if response.data and response.data[0]['tavily_api_key']:
            logging.info(f"Tavily API key found: {response.data[0]['tavily_api_key']}")
            return response.data[0]['tavily_api_key']
        else:
            raise ValueError("Tavily API key not found or empty for the user")
        
    @staticmethod
    def create_keyword_analysis(user_id, keyword_id):
        supabase = get_supabase_client()
        try:
            # Convert UUID objects to strings
            user_id_str = str(user_id) if isinstance(user_id, uuid.UUID) else user_id
            keyword_id_str = str(keyword_id) if isinstance(keyword_id, uuid.UUID) else keyword_id
            
            response = supabase.table('keyword_analysis').insert({
                'user_id': user_id_str,
                'keyword_id': keyword_id_str,
                'status': 'pending'
            }).execute()
            
            if response.data:
                return response.data[0]['id']  # This should already be a string
            else:
                raise Exception("No data returned from insert operation")
        except Exception as e:
            logging.error(f"Error creating keyword analysis: {str(e)}")
            return None
        
    @staticmethod
    def get_latest_analysis_for_keyword(keyword_id):
        supabase = get_supabase_client()
        response = supabase.table('keyword_analysis') \
            .select('*') \
            .eq('keyword_id', keyword_id) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        return response.data[0] if response.data else None
