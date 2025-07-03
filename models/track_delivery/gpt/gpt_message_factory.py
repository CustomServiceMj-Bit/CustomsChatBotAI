

import json
from pathlib import Path
from typing import List, Dict, Optional, Any

from models.track_delivery.api_spec.openai_api_spec import SYSTEM_MESSAGE, GPT_3P5_TURBO, FUNC_AUTO_OPTION

# Load function schema at module load time
def _load_function_schema_once() -> List[Dict[str, Any]]:
    try:
        path = Path(__file__).parents[2] / "resources" / "function_call" / "functions.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CRITICAL] Failed to load functions.json: {e}", flush=True)
        raise

FUNCTION_SCHEMA = _load_function_schema_once()

def build_messages(user_message: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    messages = []

    if history:
        has_system = any(msg.get("role") == "system" for msg in history)
        if not has_system:
            messages.append(SYSTEM_MESSAGE)
        messages.extend(history)
    else:
        messages.append(SYSTEM_MESSAGE)

    messages.append({"role": "user", "content": user_message})
    return messages

def build_request_body(
    model: str = GPT_3P5_TURBO,
    user_messages: Optional[List[Dict[str, str]]] = None,
    tool_choice: str = FUNC_AUTO_OPTION
) -> Dict[str, Any]:
    return {
        "model": model,
        "messages": user_messages or [],
        "functions": FUNCTION_SCHEMA,
        "function_call": tool_choice
    }