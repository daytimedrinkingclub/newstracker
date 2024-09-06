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
        
        # Get user plan type
        user_plans = DataService.get_user_plans(user_id)
        user_plan_type = user_plans[0]['plan'] if user_plans else None

        logging.info(f"User plan type: {user_plan_type}")
        
        # Determine which API key to use
        if user_plan_type == "freemium":
            keys = DataService.get_user_anthropic_keys(user_id)
        elif user_plan_type == "premium":
            keys = os.getenv("ANTHROPIC_API_KEY")
        else:
            raise ValueError(f"Unknown user plan type: {user_plan_type}")

        logging.info(f"API key retrieved: {'Yes' if keys else 'No'}")

        client = anthropic.Anthropic(api_key=keys)

        prompt = AnthropicService.prompt_selector(tool_name)
        logging.info(f"Prompt selected: {prompt[:50]}...")  # Log first 50 characters of prompt
        logging.info(f"Sending request to Anthropic API")

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