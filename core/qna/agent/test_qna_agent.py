# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.qna.agent.qna_agent import qna_agent
from core.shared.states.states import CustomsAgentState

if __name__ == "__main__":
    # Test query
    test_query = "How to declare customs?"
    state = CustomsAgentState(query=test_query)
    result = qna_agent(state)

    print("=== QNA AGENT TEST RESULT ===")
    print("Query:", test_query)
    print("\nFinal Response:", result["final_response"])
    print("\nResponse Source:", result["intermediate_results"]["qna"]["response_source"])
    print("Responses Similar:", result["intermediate_results"]["qna"]["responses_similar"])
    print("\nLLM Response:", result["intermediate_results"]["qna"]["llm_response"])
    print("\nRAG Response:", result["intermediate_results"]["qna"]["rag_response"]) 