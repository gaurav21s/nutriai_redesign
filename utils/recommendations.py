"""
Recommendations requirements:
1. Healthier alternative recommend
2. New healthy recipe recommend
"""

import openai

class OpenAIHandler:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def get_model_response(self, input_text: str) -> str:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": input_text}]
        )
        return response.choices[0].message['content']