import config
import json # For OpenAI function call args
import ai_context

# We need to import the SDKs here too to access their specific types for response construction in error cases,
# but only if they were successfully imported in config.py
genai = None
gemini_types = None
OpenAI_SDK_Class = None # Renamed for clarity to indicate it's the class
if config.genai:
    genai = config.genai
    gemini_types = config.gemini_types
if config.OpenAIClient: # Corrected to use the alias OpenAIClient from config.py
    OpenAI_SDK_Class = config.OpenAIClient 

MAX_AI_RETRIES = 1 # Try once more if the first attempt yields no text

# Helper function for AI interaction - Returns FULL RESPONSE OBJECT
def get_ai_model_response(prompt_text):
    if not config.global_ai_client:
        error_msg = f"[AI Fallback - Global AI Client not initialized for provider {config.AI_PROVIDER}. Prompt: '{prompt_text}']"
        if config.AI_PROVIDER == "GEMINI" and genai and gemini_types:
            error_part = gemini_types.Part(text=error_msg)
            error_content = gemini_types.Content(parts=[error_part], role="model")
            mock_candidate = gemini_types.Candidate(content=error_content, finish_reason=gemini_types.FinishReason.ERROR, safety_ratings=[])
            return gemini_types.GenerateContentResponse(prompt_feedback=None, candidates=[mock_candidate])
        else: # OpenAI or if Gemini types are not available
            # For OpenAI, a simple dict mimicking error is fine, or a more structured one if we define it
            return {"error_message": error_msg, "choices": []} 

    for attempt in range(MAX_AI_RETRIES + 1):
        if config.DEBUG_MODE:
            print(f"DEBUG: AI Provider: {config.AI_PROVIDER}, Prompt (Attempt {attempt + 1}): {prompt_text[:200]}...")
        try:
            if config.AI_PROVIDER == "GEMINI":
                response = config.global_ai_client.generate_content(
                    contents=prompt_text,
                    generation_config=config.gemini_generation_config # Use Gemini specific config
                )
                if config.DEBUG_MODE: print(f"DEBUG: Gemini Response object received.")
                # Basic validation for Gemini response structure
                if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                    if attempt < MAX_AI_RETRIES: continue
                    return {"error_message": "[AI Error - Gemini response missing content parts]", "candidates": []}
                return response
            
            elif config.AI_PROVIDER == "OPENAI":
                if not OpenAI_SDK_Class: # Check if OpenAI SDK class was actually loaded
                    return {"error_message": "[AI Error - OpenAI SDK not available but selected as provider]", "choices": []}
                
                # System message is identical across every call this session so
                # providers can cache the prefix. Keep dynamic context in the
                # user turn only.
                messages = [
                    {"role": "system", "content": ai_context.SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt_text}
                ]
                api_call_params = {
                    "model": config.OPENAI_MODEL_NAME,
                    "messages": messages,
                    "temperature": 0.7, # Can be in config later
                    "max_tokens": 1024   # Can be in config later
                }
                if config.openai_tools_list:
                    api_call_params["tools"] = config.openai_tools_list
                    api_call_params["tool_choice"] = "auto" # or "any" to force, or specific func
                
                response = config.global_ai_client.chat.completions.create(**api_call_params)
                if config.DEBUG_MODE: print(f"DEBUG: OpenAI Response object received.")
                # Basic validation for OpenAI response structure
                if not response.choices or not response.choices[0].message:
                    if attempt < MAX_AI_RETRIES: continue
                    return {"error_message": "[AI Error - OpenAI response missing choices or message]", "choices": []}
                return response
            
            else:
                return {"error_message": f"[AI Error - Unknown AI_PROVIDER: {config.AI_PROVIDER}]", "candidates": [], "choices": []}

        except Exception as e:
            print(f"Error during AI model call with {config.AI_PROVIDER}: {e}")
            if config.DEBUG_MODE: import traceback; traceback.print_exc()
            if attempt < MAX_AI_RETRIES:
                if config.DEBUG_MODE: print(f"DEBUG: Retrying AI call...")
                continue
            else:
                return {"error_message": f"[AI Error after {MAX_AI_RETRIES+1} attempts with {config.AI_PROVIDER}: {e}]", "candidates": [], "choices": []}
    
    # Fallback if loop completes unexpectedly
    return {"error_message": f"[AI Error - Unexpected exit from retry loop for {config.AI_PROVIDER}]", "candidates": [], "choices": []}

