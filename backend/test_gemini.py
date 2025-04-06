import google.generativeai as genai
import os

# Replace with your actual API key
API_KEY = "YOUR GEMINI API KEY"
genai.configure(api_key=API_KEY)

# List available models to see what's accessible
print("Available models:")
for m in genai.list_models():
    print(f"- {m.name}")

try:
    # Test the model
    model = genai.GenerativeModel('models/gemini-1.5-pro')
    response = model.generate_content("Tell me about photosynthesis")
    print("\nResponse:")
    print(response.text)
except Exception as e:
    print(f"\nError: {str(e)}")