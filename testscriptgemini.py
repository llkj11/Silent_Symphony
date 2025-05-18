from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyDE6KqtzgaRjp_PppUDYbctJxpKbqmvrsw")

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)

# Option B: Pass directly to client (if supported by the specific client constructor you use)
# client = genai.Client(api_key=API_KEY) # This is shown in some docs