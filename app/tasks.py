from .models.data_service import DataService
from .services.agent import AnthropicChat
from flask import current_app

def analyze_keyword(anthropic_api_key, keyword, analysis_id):
    print(f"Starting analyze_keyword with analysis_id: {analysis_id}, keyword: {keyword}")
    try:
        # Update analysis status to 'in_progress'
        update_success = DataService.update_analysis_status(analysis_id, 'in_progress')
        print(f"Updated analysis status to 'in_progress': {update_success}")
        
        # Start the analysis
        response = AnthropicChat.handle_chat(analysis_id, keyword, anthropic_api_key)
        
        if response['status'] == 'completed':
            # Update the keyword summary with the final results
            update_success = DataService.update_keyword_summary(
                analysis_id,
                news_summary=response.get('news_summary', ''),
                positive_summary=response.get('positive_summary', ''),
                negative_summary=response.get('negative_summary', ''),
                positive_sources_links=response.get('positive_sources_links', ''),
                negative_sources_links=response.get('negative_sources_links', '')
            )
            
            if not update_success:
                raise Exception("Failed to update keyword summary")
            
            # Update analysis status to 'completed'
            DataService.update_analysis_status(analysis_id, 'completed')
        else:
            # If not completed, update status to 'in_progress'
            DataService.update_analysis_status(analysis_id, 'in_progress')
        
        print(f"analyze_keyword completed for analysis_id: {analysis_id}")
        
    except Exception as e:
        print(f"Error in analyze_keyword task: {str(e)}")
        # Update the analysis status to indicate failure
        update_success = DataService.update_analysis_status(analysis_id, 'failed')
        print(f"Updated analysis status to 'failed': {update_success}")