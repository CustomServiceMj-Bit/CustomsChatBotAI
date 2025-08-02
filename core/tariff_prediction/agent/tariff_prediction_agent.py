from typing import Dict, Any, List, Optional
import re
from dataclasses import dataclass, field

from core.shared.states.states import CustomsAgentState
from core.tariff_prediction.tools.calculate_tariff_amount import calculate_tariff_amount
from core.tariff_prediction.tools.detect_scenario import detect_scenario_from_input
from core.tariff_prediction.tools.parse_user_input import parse_user_input
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.tariff_prediction.constants import (
    SUPPORTED_COUNTRIES, OFF_TOPIC_KEYWORDS, CORRECTION_KEYWORDS, 
    SESSION_TERMINATION_KEYWORDS, SIMPLE_TARIFF_REQUESTS, 
    TARIFF_CONTEXT_KEYWORDS, DEFAULT_EXCHANGE_RATES,
    DEFAULT_COUNTRY, DEFAULT_QUANTITY, DEFAULT_SHIPPING_COST, DEFAULT_SESSION_ID,
    ERROR_MESSAGES, CORRECTION_MESSAGES, RESPONSE_MESSAGES, STATE_KEYS, STEPS, LLM_PROMPTS
)
from core.tariff_prediction.tools.context_utils import extract_llm_response, extract_info_from_context, merge_context_with_current
from core.tariff_prediction.agent.step_api import tariff_prediction_step_api
from core.tariff_prediction.dto.tariff_request import TariffPredictionRequest
from core.tariff_prediction.dto.tariff_response import TariffPredictionResponse
from .workflow import TariffPredictionWorkflow, WorkflowManager, workflow_manager
from .utils import get_or_create_workflow, extract_context_from_messages, run_workflow_with_context, build_response_state

# tariff_prediction_agent orchestrator만 남김
def tariff_prediction_agent(state: CustomsAgentState) -> CustomsAgentState:
    workflow = get_or_create_workflow(state)
    context = extract_context_from_messages(state.get("messages", []))
    response = run_workflow_with_context(workflow, state, context)
    return build_response_state(state, response)