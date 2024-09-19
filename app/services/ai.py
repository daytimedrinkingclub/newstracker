import logging
import os
import anthropic
from ..models.data_service import DataService

class AnthropicService:
    @staticmethod
    def load_prompt(tool_name):
        if tool_name == "negative_summary":
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', f'negative_prompt.txt')
        elif tool_name == "positive_summary":
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', f'postive_prompt.txt')
        else:
            raise ValueError(f"Unknown tool name: {tool_name}")
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()

    @staticmethod
    def prompt_selector(tool_name):
        print(f"Prompt selector called with tool name: {tool_name}")
        if tool_name in ["negative_summary", "positive_summary"]:
            print("toolll name ", tool_name)
            return AnthropicService.load_prompt(tool_name)
        else:
            raise ValueError(f"Unknown tool name: {tool_name}")

    @staticmethod
    def call_anthropic(tool_name, user_message, user_id):
        logging.info(f"Calling Anthropic for tool: {tool_name}")
        
        # Get user plan type
        user_plans = DataService.get_user_plans(user_id)
        user_plan_type = user_plans[0]['plan'] if user_plans else None

        # Determine which API key to use
        if user_plan_type == "freemium":
            keys = DataService.get_user_anthropic_keys(user_id)
            
        elif user_plan_type in ["premium", "paid"]:
            keys = os.getenv("ANTHROPIC_API_KEY")
        else:
            raise ValueError(f"Unknown user plan type: {user_plan_type}")
        
        client = anthropic.Anthropic(api_key=keys)

        prompt = AnthropicService.prompt_selector(tool_name)
        logging.info(f"Prompt: {prompt}")
        
        # Adjust max_tokens based on the input length
        input_length = len(user_message)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=prompt,
            temperature=0,
            messages=[
                {"role": "user", "content": user_message}  # Limit user message to 4000 characters
            ]
        )

        result = response.content[0].text  # Limit response to 4000 characters
        logging.info(f"Anthropic response length: {len(result)} characters")
        return result