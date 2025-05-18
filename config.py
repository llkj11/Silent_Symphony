try:
    import google.genai as genai
    from google.genai import types
    print(f"SDK Version (config.py): {genai.__version__}")
except ImportError:
    print("Google GenAI SDK (google-genai) not installed or module structure changed. Please ensure it is installed correctly: pip install google-genai")
    genai = None
    types = None

# --- Configuration ---
DEBUG_MODE = False # Set to True to enable debug prints for AI calls
# IMPORTANT: Replace 'YOUR_API_KEY' with your actual Google AI Studio API key.
# You can also set the GOOGLE_API_KEY environment variable.
API_KEY = 'AIzaSyDE6KqtzgaRjp_PppUDYbctJxpKbqmvrsw'
AI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" # Updated to specific 2.5 Flash preview model

# Initialize Google AI Client
global_ai_client = None
global_generation_config = None
# global_safety_settings = None # Kept commented as in original

if genai and types and API_KEY and API_KEY != 'YOUR_API_KEY':
    try:
        global_ai_client = genai.Client(api_key=API_KEY)
        
        # Use GenerateContentConfig
        global_generation_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1024 # Increased from 150
            # automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True) # Temporarily removed
        )
        print("Initialized GenerateContentConfig (temp=0.7, max_tokens=1024) in config.py.")

        # global_safety_settings definition remains, but not passed to generate_content if problematic.
        # global_safety_settings = [
        #      types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        #      # ... other settings
        # ]

        print(f"Successfully initialized AI Client for model: {AI_MODEL_NAME} in config.py. Using updated GenerateContentConfig.")

    except AttributeError as ae:
        print(f"Error initializing Google AI Client in config.py (AttributeError): {ae}")
        print("This might indicate an issue with the google-genai SDK version (e.g. GenerateContentConfig fields). AI features will use fallback.")
        global_ai_client = None
        global_generation_config = None
    except Exception as e:
        print(f"Error initializing Google AI Client in config.py: {e}")
        global_ai_client = None
        global_generation_config = None
elif not (genai and types):
    print("Skipping AI initialization in config.py as the SDK (google.genai or types) is not available.")
elif API_KEY == 'YOUR_API_KEY':
    print("Skipping AI initialization in config.py. API_KEY is still the placeholder 'YOUR_API_KEY'.") 