import logging
import os
import anthropic
from ..models.data_service import DataService

class AnthropicService:
    @staticmethod
    def load_prompt(tool_name):
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', f'{tool_name}.txt')
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()

    @staticmethod
    def prompt_selector(tool_name):
        if tool_name in ["negative_prompt", "positive_prompt"]:
            return AnthropicService.load_prompt(tool_name)
        else:
            raise ValueError(f"Unknown tool name: {tool_name}")

    @staticmethod
    def call_anthropic(tool_name, user_message, user_id):
        logging.info(f"Calling Anthropic for tool: {tool_name}")
        logging.info(f"User plan type: {user_plan_type}")
        logging.info(f"API key retrieved: {'Yes' if keys else 'No'}")
        logging.info(f"Prompt selected: {prompt[:50]}...")  # Log first 50 characters of prompt
        logging.info(f"Sending request to Anthropic API")
        
        # check the user plan if free get keys from table if paid us os.environ
        user_plan_type = DataService.get_user_plans(user_id)
        if user_plan_type == "free":
            keys = DataService.get_user_anthropic_keys(user_id)
        elif user_plan_type == "paid":
            keys = os.getenv("ANTHROPIC_API_KEY")
        
        client = anthropic.Anthropic(api_key=keys)

        prompt = AnthropicService.prompt_selector(tool_name)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            system=prompt,
            temperature=0,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        logging.info(f"Response received from Anthropic API")
        return response.content[0].text