import os
try:
    import google.generativeai as genai
    from google.generativeai import types
    print(f"SDK Version: {genai.__version__}") # Let's try to print the version
except ImportError:
    print("Failed to import google.generativeai. Make sure it's installed.")
    exit()

# Try to get API key from environment variable first, then a placeholder
API_KEY = os.getenv('GOOGLE_API_KEY', 'YOUR_TEST_API_KEY') # Replace with your key for a real test

if API_KEY == 'YOUR_TEST_API_KEY' and 'AIzaSyDE6KqtzgaRjp_PppUDYbctJxpKbqmvrsw' != 'YOUR_API_KEY': # Check if user has a key
    print("Using your actual API Key for the test.")
    API_KEY = 'AIzaSyDE6KqtzgaRjp_PppUDYbctJxpKbqmvrsw' # Using the key from GameTest.py
elif API_KEY == 'YOUR_TEST_API_KEY':
    print("WARNING: GOOGLE_API_KEY environment variable not found, and no hardcoded key. API calls will likely fail.")


print(f"Attempting to initialize client with API_KEY: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if API_KEY else 'Not Set'}")

try:
    print("\nAttempt 1: Initialize with genai.configure() and then GenerativeModel")
    genai.configure(api_key=API_KEY)
    
    # Define generation_config with ThinkingConfig
    print("Defining generation_config with ThinkingConfig...")
    generation_config_with_thinking = types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=10, # Small for test
        thinking_config=types.ThinkingConfig(thinking_budget=0) 
    )
    print("generation_config with ThinkingConfig defined.")

    # Define safety_settings
    print("Defining safety_settings...")
    safety_settings_list = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    ]
    print("safety_settings list defined.")

    print("Initializing GenerativeModel with all configs...")
    model_test = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-04-17",
        generation_config=generation_config_with_thinking,
        safety_settings=safety_settings_list
    )
    print("GenerativeModel initialized successfully (Attempt 1).")
    print("Making a test API call...")
    response = model_test.generate_content("test")
    print(f"Test API call response: {response.text[:50]}...")

except AttributeError as ae:
    print(f"Caught AttributeError (Attempt 1): {ae}")
except Exception as e:
    print(f"Caught other Exception (Attempt 1): {e}")


# This is the example from your documentation for "Set budget on thinking models"
# Using client.models.generate_content()
print("\nAttempt 2: Using client = genai.Client() and client.models.generate_content()")
try:
    # client = genai.Client() # This would use GOOGLE_API_KEY from env
    client = genai.Client(api_key=API_KEY) # Explicitly provide key
    print("genai.Client initialized.")

    print("Defining config for client.models.generate_content...")
    # The documentation for client.models.generate_content uses 'config=' for the whole GenerationConfig object
    # but inside that, it nests thinking_config. Let's align with the doc for this specific call.
    # However, the SDK typically uses 'generation_config' as the parameter name for the GenerationConfig object.
    # Let's try what's in your doc screenshot `config=types.GenerateContentConfig(...)` where GenerateContentConfig is an alias for GenerationConfig
    # And the SDK for client.models.generate_content indeed might take a `generation_config` parameter not `config`
    # For safety, I will use `generation_config` as that's more standard across the SDK.
    
    generation_param_for_client_models = types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=10,
        thinking_config=types.ThinkingConfig(thinking_budget=1024) # Using 1024 as per docs example
    )
    
    safety_settings_for_client_models = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    ]

    print("Making a test API call with client.models.generate_content...")
    response_client_models = client.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents="test",
        generation_config=generation_param_for_client_models, 
        safety_settings=safety_settings_for_client_models
    )
    print(f"Test API call (client.models.generate_content) response: {response_client_models.text[:50]}...")
    print("client.models.generate_content with ThinkingConfig and SafetySetting seems to have worked (Attempt 2).")

except AttributeError as ae:
    print(f"Caught AttributeError (Attempt 2 for client.models.generate_content): {ae}")
except Exception as e:
    print(f"Caught other Exception (Attempt 2 for client.models.generate_content): {e}")

print("\n--- Test Finished ---") 