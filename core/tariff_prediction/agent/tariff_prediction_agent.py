from langchain.agents import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm
from core.tariff_prediction.tools.calculate_tariff import calculate_tariff
from core.tariff_prediction.tools.get_exchange_rate import get_exchange_rate
from core.tariff_prediction.tools.get_product_classification import get_product_classification

def tariff_prediction_agent(state: CustomsAgentState) -> CustomsAgentState:
   tools = [calculate_tariff, get_product_classification, get_exchange_rate] # 관세 예측 + HS 코드 조회 + 환율 조회
   llm = get_llm()
   system_message = SystemMessage(content="""
당신은 관세 예측 전문 에이전트입니다.
사용자가 제공하는 상품 관련 정보를 바탕으로 정확한 관세 예측과 관련된 정보를 제공하세요. 
다음 도구들을 사용하여 사용자의 요청을 처리할 수 있습니다:

1. **get_product_classification**:
   - 상품명을 기반으로 **HS 코드**를 조회합니다.
   - 예시: "노트북" → "8471.30.00"
   - 사용자가 상품명을 제공하면 해당 도구를 통해 **HS 코드**를 추출하세요.

2. **calculate_tariff**:
   - **HS 코드**, **상품 가격**, **원산지**를 기반으로 **관세**를 계산합니다.
   - 예시: HS 코드 '8471.30.00', 가격 1500달러, 원산지 'Japan' → 예상 관세 계산
   - 사용자가 **상품 코드**(HS 코드), **가격**(USD), **원산지**를 제공하면, 해당 도구로 **관세**를 계산하세요.
   - 이 도구는 상품의 가격과 원산지가 필요하므로 반드시 이들 정보가 제공되었을 때만 호출하세요.

3. **get_exchange_rate**:
   - 특정 **통화**와 **KRW**(한국 원화) 간의 환율을 조회합니다.
   - 예시: "USD/KRW 환율"
   - 사용자가 **USD**, **JPY**, **EUR** 등 **통화**를 제공하면 해당 통화와 **KRW** 간의 환율을 조회할 수 있습니다.

### 흐름 유도:
- **상품명**이 주어졌다면 먼저 `get_product_classification` 도구를 사용하여 **HS 코드**를 추출하세요.
- **HS 코드**, **가격**, **원산지**가 제공되었다면, `calculate_tariff` 도구를 사용하여 **예상 관세**를 계산하세요.
- **외화**가 주어졌다면 `get_exchange_rate` 도구를 사용하여 **환율** 정보를 제공하세요.
- 가능한 경우 **모든 도구**를 사용하여 **종합적인 답변**을 제공하세요. """)

   react_agent = create_react_agent(llm, tools)
   
   messages = [system_message, HumanMessage(content=state["query"])]
   result = react_agent.invoke({"messages": messages})
   
   state["final_response"] = result["messages"][-1].content
   return state