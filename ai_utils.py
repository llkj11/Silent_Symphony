import config

MAX_AI_RETRIES = 1 # Try once more if the first attempt yields no text

# Helper function for AI interaction ---
def get_ai_description(prompt_text):
    if not config.global_ai_client or not config.global_generation_config:
        return f"[AI Fallback - Client or GenConfig not initialized. Original prompt: '{prompt_text}'] ... A generic description unfolds."
    
    for attempt in range(MAX_AI_RETRIES + 1):
        if config.DEBUG_MODE:
            print(f"DEBUG: AI Prompt (Attempt {attempt + 1}/{MAX_AI_RETRIES + 1}): {prompt_text[:100]}...")
        try:
            response = config.global_ai_client.models.generate_content(
                model=config.AI_MODEL_NAME,
                contents=prompt_text,
                config=config.global_generation_config
            )

            if config.DEBUG_MODE:
                print(f"DEBUG: Raw AI Response object: {type(response)}")
                # Check for prompt feedback (blocking)
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_message = response.prompt_feedback.block_reason_message or "No specific message."
                    print(f"DEBUG: Warning: AI prompt was blocked. Reason: {response.prompt_feedback.block_reason}, Message: {block_reason_message}")
                # print(f"DEBUG: Full AI Response: {response}") # Usually too verbose
                if hasattr(response, 'candidates') and response.candidates:
                    print(f"DEBUG: Finish Reason for first candidate: {response.candidates[0].finish_reason}")

            # Check for prompt feedback (blocking) - This check should happen regardless of DEBUG_MODE for actual blocking
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = response.prompt_feedback.block_reason_message or "No specific message."
                # We already printed in debug, but for actual game flow:
                # print(f"Warning: AI prompt was blocked. Reason: {response.prompt_feedback.block_reason}, Message: {block_reason_message}") 
                return f"[AI prompt blocked: {response.prompt_feedback.block_reason}. Original prompt: '{prompt_text}']"

            text_output = None
            if response.text:
                text_output = response.text.strip()
                if config.DEBUG_MODE:
                    print(f"DEBUG: response.text is available: '{text_output[:100]}...'")
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts and response.candidates[0].content.parts[0].text:
                text_output = response.candidates[0].content.parts[0].text.strip()
                if config.DEBUG_MODE:
                    print(f"DEBUG: Text found in response.candidates: '{text_output[:100]}...'")
            else:
                if config.DEBUG_MODE:
                    print("DEBUG: Warning: AI response seems to have no text content in expected fields (response.text or response.candidates).")
                    print(f"DEBUG: Available candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
                return f"[AI response had no text. Original prompt: '{prompt_text}']"
            
            if text_output:
                if config.DEBUG_MODE: print(f"DEBUG: AI Response Text (Attempt {attempt+1}): '{text_output[:100]}...'")
                return text_output # Success, return the text
            else:
                # No text output, will loop to retry if attempts remain
                if config.DEBUG_MODE:
                    print(f"DEBUG: AI response had no text on attempt {attempt + 1}.")
                    print(f"DEBUG: Full response object on empty text: {response}") # Log full response for debugging empty text
        
        except AttributeError as ae:
            # Specifically catch if types.SafetySetting was the issue during the actual call
            # Assuming 'genai' is available in the scope where this function is defined, if needed for `genai.__version__`
            # For now, removing direct dependency on genai and types from config.py's top level for this error message construction to simplify.
            if "SafetySetting" in str(ae) and "not found in types" in str(ae).lower(): # Heuristic check
                 print(f"AI Call Error: types.SafetySetting seems to be unavailable or used incorrectly. Please check SDK docs.") # Simplified message
            else:
                 print(f"AI Call Error (AttributeError): {ae}")
            # Don't retry on attribute errors, it's likely a code/SDK issue
            return f"[AI Error - AttributeError during call. Prompt: '{prompt_text}'] ... The details are unclear."
        except Exception as e:
            print(f"Error getting AI description: {e}")
            if attempt < MAX_AI_RETRIES:
                if config.DEBUG_MODE: print(f"DEBUG: Retrying AI call after error ({e})...")
                continue # Retry if there are attempts left
            return f"[AI Error: Could not generate description for: '{prompt_text}'] ... The details are hazy."
        
        # If loop finishes without returning text (e.g. max retries for empty text reached)
        if attempt == MAX_AI_RETRIES and not text_output:
            if config.DEBUG_MODE:
                print(f"DEBUG: AI failed to produce text after {MAX_AI_RETRIES + 1} attempts.")
            return f"[AI response had no text. Original prompt: '{prompt_text}']"
    
    # Fallback if something goes wrong with the loop logic, should not be reached ideally
    return f"[AI response had no text after all attempts. Original prompt: '{prompt_text}']" 