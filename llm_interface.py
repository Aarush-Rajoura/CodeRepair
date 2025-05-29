import google.generativeai as genai
from google.genai import types
class GeminiLLM:
    def __init__(self, api_key: str, model: str = 'gemini-2.0-flash'):

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model,
        generation_config={
        "temperature": 0.2,
        "max_output_tokens": 512
    })

    def generate(self, prompt: str, temperature: float = 0.2, max_output_tokens: int = 512) -> str:

        response = self.model.generate_content(
            contents=prompt,
            generation_config=self.model._generation_config  
        )
        if hasattr(response, 'text'):
            return response.text
       
        return str(response)
