import logging
import os
import anthropic
from ..models.data_service import DataService
from ..utils.rate_limiter import RateLimiter, exponential_backoff

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
    @RateLimiter(max_calls=5, period=60)  # 10 calls per minute
    @exponential_backoff(max_retries=3, base_delay=2)
    def call_anthropic(tool_name, user_message, user_id):
        logging.info(f"Calling Anthropic for tool: {tool_name}")
        
        # Get user plan type
        user_plans = DataService.get_user_plans(user_id)
        user_plan_type = user_plans[0]['plan'] if user_plans else None

        # Determine which API key to use
        if user_plan_type == "freemium":
            keys = DataService.get_user_anthropic_keys(user_id)
        elif user_plan_type == "premium":
            keys = os.getenv("ANTHROPIC_API_KEY")
        else:
            raise ValueError(f"Unknown user plan type: {user_plan_type}")

        client = anthropic.Anthropic(api_key=keys)

        prompt = AnthropicService.prompt_selector(tool_name)
        logging.info(f"Prompt: {prompt}")
        
        # Adjust max_tokens based on the input length
        input_length = len(user_message)
        max_tokens = min(4000, max(1000, input_length * 2))  # Adjust this formula as needed
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=max_tokens,
            system=prompt,
            temperature=0,
            messages=[
                {"role": "user", "content": user_message[:4000]}  # Limit user message to 4000 characters
            ]
        )

        result = response.content[0].text[:4000]  # Limit response to 4000 characters
        logging.info(f"Anthropic response length: {len(result)} characters")
        return result