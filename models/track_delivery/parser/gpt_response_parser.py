from typing import Dict, Any, List

def extract_message(gpt_response: Dict[str, Any]) -> Dict[str, Any] | None:
    choices: List[Dict[str, Any]] = gpt_response.get("choices")
    if not choices:
        return None

    return choices[0].get("message")