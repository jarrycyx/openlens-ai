from litellm.integrations.custom_logger import CustomLogger
import litellm
import json
import os
from datetime import datetime
import uuid

# This file includes the custom callbacks for LiteLLM Proxy
# Once defined, these can be passed in proxy_config.yaml

# Create output directory for logged calls
LOGGED_CALLS_DIR = "outputs/logged_calls_1219"
os.makedirs(LOGGED_CALLS_DIR, exist_ok=True)

def convert_to_dict(obj, max_depth=10, current_depth=0):
    """Recursively convert objects to dictionaries with maximum recursion depth control
    
    Args:
        obj: The object to convert
        max_depth: Maximum recursion depth to prevent infinite recursion (default: 10)
        current_depth: Current recursion depth (used internally)
    
    Returns:
        Converted dictionary or the original object if max depth is reached
    """
    # Check if we've reached the maximum recursion depth
    if current_depth >= max_depth:
        # Return a string representation instead of recursing further
        return str(obj)
    
    if isinstance(obj, dict):
        return {k: convert_to_dict(v, max_depth, current_depth + 1) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_dict(item, max_depth, current_depth + 1) for item in obj]
    elif hasattr(obj, '__dict__'):
        return convert_to_dict(obj.__dict__, max_depth, current_depth + 1)
    elif hasattr(obj, '_asdict'):  # namedtuple
        return convert_to_dict(obj._asdict(), max_depth, current_depth + 1)
    else:
        return obj

def save_call_to_json(call_data, call_type):
    """Save API call data to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    day_str = datetime.now().strftime("%Y%m%d")
    call_id = str(uuid.uuid4())
    
    filename = f"{call_type}_{timestamp}"
    filepath = os.path.join(LOGGED_CALLS_DIR, day_str, f"{filename}.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(call_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Saved {call_type} call to {filepath}")
    except Exception as e:
        print(f"Error saving {call_type} call to JSON: {e}")

class MyCustomHandler(CustomLogger):

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        print(f"On Async Success!")
        
        
        # Save async success event data to JSON
        try:
            async_success_data = {
                "args": convert_to_dict(kwargs),
                "response": convert_to_dict(response_obj),
                "start_time": start_time,
                "end_time": end_time
            }
            save_call_to_json(async_success_data, "succ")
        except Exception as e:
            print(f"Error in async_log_success_event: {e}")
        
        return

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time): 
        try:
            print(f"On Async Failure !")
            # Save async failure event data to JSON
            try:
                async_failure_data = {
                    "args": convert_to_dict(kwargs),
                    "response": convert_to_dict(response_obj),
                    "start_time": start_time,
                    "end_time": end_time
                }
                save_call_to_json(async_failure_data, "fail")
            except Exception as save_error:
                print(f"Error saving async failure data: {save_error}")
                
        except Exception as e:
            print(f"Exception: {e}")

proxy_handler_instance = MyCustomHandler()

# Set litellm.callbacks = [proxy_handler_instance] on the proxy
# need to set litellm.callbacks = [proxy_handler_instance] # on the proxy