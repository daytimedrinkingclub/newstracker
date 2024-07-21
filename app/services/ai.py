import os
import anthropic

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
    def call_anthropic(tool_name, user_message):
        prompt = AnthropicService.prompt_selector(tool_name)
        response = anthropic.Anthropic().messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            system=prompt,
            temperature=0,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return response.content[0].text