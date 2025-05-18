import os             # For accessing environment variables
from dotenv import load_dotenv # For loading .env file
import copy # For deep copying schemas before modification

load_dotenv() # Load variables from .env file into environment

# --- AI Provider Configuration ---
# Set this to "GEMINI" or "OPENAI" to choose the AI provider
AI_PROVIDER = "OPENAI" # For testing OpenAI path now
# Or load from .env: AI_PROVIDER = os.getenv("AI_PROVIDER", "GEMINI").upper()

# --- Gemini Configuration (if used) ---
try:
    import google.genai as genai # This is the primary import
    from google.genai import types as gemini_types
    print(f"SDK Version (config.py): {genai.__version__}")
except ImportError:
    print("Google GenAI SDK (google-genai) not installed. AI features may be limited or unavailable.")
    genai = None
    gemini_types = None

# --- OpenAI Configuration (if used) ---
try:
    from openai import OpenAI as OpenAIClient
    print(f"OpenAI SDK imported successfully.")
except ImportError:
    print("OpenAI SDK not installed. OpenAI provider will be unavailable.")
    OpenAIClient = None # So we can check for its existence

# Import our function declarations
GAME_EVENT_TOOLS = None
TOOL_CONFIG = None
if genai and gemini_types: # Check if SDK and types loaded
    try:
        from ai_function_declarations import (
            LIST_POINTS_OF_INTEREST_DECLARATION,
            PLAYER_DISCOVERS_ITEM_DECLARATION,
            PLAYER_ENCOUNTERS_ENEMY_DECLARATION,
            NARRATIVE_OUTCOME_DECLARATION
        )
        GAME_EVENT_TOOLS = gemini_types.Tool(function_declarations=[
            LIST_POINTS_OF_INTEREST_DECLARATION,
            PLAYER_DISCOVERS_ITEM_DECLARATION,
            PLAYER_ENCOUNTERS_ENEMY_DECLARATION,
            NARRATIVE_OUTCOME_DECLARATION
        ])
        TOOL_CONFIG = gemini_types.ToolConfig(function_calling_config=gemini_types.FunctionCallingConfig(mode="ANY"))
    except ImportError as e:
        print(f"Could not import AI function declarations: {e}. Function calling will be disabled.")
    except AttributeError as e:
        print(f"AttributeError while setting up tools (likely SDK version issue with types.Tool or ToolConfig): {e}. Function calling may be affected.")
        GAME_EVENT_TOOLS = None
        TOOL_CONFIG = None

# --- Configuration ---
DEBUG_MODE = True # Set to True to enable debug prints for AI calls

# API_KEY is now loaded from .env
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Model Names --- (Provider-specific)
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest" # Changed to 1.5 for better function calling
OPENAI_MODEL_NAME = "gpt-4.1" # Target model, can be changed to gpt-4o or gpt-4-turbo if needed

# --- Load Raw Function Declarations ---
RAW_FUNCTION_DECLARATIONS = []
if genai or OpenAIClient: # Check if any SDK is available to justify loading declarations
    try:
        from ai_function_declarations import (
            LIST_POINTS_OF_INTEREST_DECLARATION,
            PLAYER_DISCOVERS_ITEM_DECLARATION,
            PLAYER_ENCOUNTERS_ENEMY_DECLARATION,
            NARRATIVE_OUTCOME_DECLARATION
        )
        RAW_FUNCTION_DECLARATIONS = [
            LIST_POINTS_OF_INTEREST_DECLARATION,
            PLAYER_DISCOVERS_ITEM_DECLARATION,
            PLAYER_ENCOUNTERS_ENEMY_DECLARATION,
            NARRATIVE_OUTCOME_DECLARATION
        ]
    except ImportError as e:
        print(f"Could not import AI function declarations: {e}. Function calling will be disabled.")

# --- Helper to convert schema types for OpenAI ---
def _convert_schema_types_to_lowercase(schema_part):
    if isinstance(schema_part, dict):
        new_dict = {}
        for k, v in schema_part.items():
            if k == "type" and isinstance(v, str):
                # Specific type conversions for OpenAI
                if v == "OBJECT": new_dict[k] = "object"
                elif v == "STRING": new_dict[k] = "string"
                elif v == "ARRAY": new_dict[k] = "array"
                elif v == "NUMBER": new_dict[k] = "number" # OpenAI uses 'number' for float/int
                elif v == "INTEGER": new_dict[k] = "integer" # OpenAI also supports 'integer'
                elif v == "BOOLEAN": new_dict[k] = "boolean"
                else: new_dict[k] = v # Keep other types as is (e.g. custom enums if any)
            else:
                new_dict[k] = _convert_schema_types_to_lowercase(v)
        return new_dict
    elif isinstance(schema_part, list):
        return [_convert_schema_types_to_lowercase(item) for item in schema_part]
    else:
        return schema_part

# --- Global AI Client and Provider-Specific Tool/Config Variables ---
DEBUG_MODE = True 
global_ai_client = None
# For Gemini
gemini_generation_config = None 
# For OpenAI
openai_tools_list = None # This will be the list of formatted tool dicts for OpenAI

# --- Initialize based on AI_PROVIDER ---
if AI_PROVIDER == "GEMINI":
    if genai and gemini_types and GEMINI_API_KEY and GEMINI_API_KEY != 'YOUR_API_KEY':
        try:
            global_ai_client = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME)
            
            gemini_sdk_tools = None
            gemini_tool_config = None
            if RAW_FUNCTION_DECLARATIONS:
                # RAW_FUNCTION_DECLARATIONS are already Python dicts, suitable for function_declarations arg
                gemini_sdk_tools = [gemini_types.Tool(function_declarations=RAW_FUNCTION_DECLARATIONS)]
                gemini_tool_config = gemini_types.ToolConfig(function_calling_config=gemini_types.FunctionCallingConfig(mode="ANY"))

            config_dict = {
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
            if gemini_sdk_tools:
                config_dict["tools"] = gemini_sdk_tools
            if gemini_tool_config:
                config_dict["tool_config"] = gemini_tool_config
            
            gemini_generation_config = gemini_types.GenerationConfig(**config_dict)
            print(f"Successfully initialized Gemini AI Model: {GEMINI_MODEL_NAME}.")
            if gemini_tool_config and gemini_sdk_tools: print(f"Gemini Function calling mode: {gemini_tool_config.function_calling_config.mode}")

        except Exception as e:
            print(f"Error initializing Gemini AI Client/Model: {e}")
            if DEBUG_MODE: import traceback; traceback.print_exc()
            global_ai_client = None
    elif not GEMINI_API_KEY or GEMINI_API_KEY == 'YOUR_API_KEY': 
        print("Skipping Gemini AI initialization. GOOGLE_API_KEY not found or is placeholder.")
    else:
        print("Skipping Gemini AI initialization as google-genai SDK is not available.")

elif AI_PROVIDER == "OPENAI":
    if OpenAIClient and OPENAI_API_KEY:
        try:
            global_ai_client = OpenAIClient(api_key=OPENAI_API_KEY)
            
            if RAW_FUNCTION_DECLARATIONS:
                openai_tools_list = []
                for raw_decl_dict in RAW_FUNCTION_DECLARATIONS:
                    # Deep copy before modifying to keep RAW_FUNCTION_DECLARATIONS pristine for Gemini
                    decl_for_openai = _convert_schema_types_to_lowercase(copy.deepcopy(raw_decl_dict))
                    openai_tools_list.append({"type": "function", "function": decl_for_openai})
            
            print(f"Successfully initialized OpenAI Client. Target model: {OPENAI_MODEL_NAME}.")
            if openai_tools_list: print("OpenAI function tools prepared with lowercase types.")

        except Exception as e:
            print(f"Error initializing OpenAI Client: {e}")
            if DEBUG_MODE: import traceback; traceback.print_exc()
            global_ai_client = None
    elif not OPENAI_API_KEY:
        print("Skipping OpenAI AI initialization. OPENAI_API_KEY not found in .env.")
    else:
        print("Skipping OpenAI AI initialization as OpenAI SDK is not available.")
else:
    print(f"Invalid AI_PROVIDER: {AI_PROVIDER}. Please choose 'GEMINI' or 'OPENAI'.")

# For ai_utils.py to access the correct config based on provider
# We can pass the specific config object or have ai_utils check AI_PROVIDER too.
# For simplicity now, ai_utils will check AI_PROVIDER and use what it needs from here.
# So, global_generation_config is for Gemini, openai_tools_list is for OpenAI. 