import sys
sys.path.append('.')  # 루트에서 실행 시 모듈 경로 문제 방지

from core.graphs.runner import run_customs_agent

QUESTIONS = [
    '간이통관이 뭐야?',
    '곤약젤리 가져와도 돼?'
]

def test_langgraph_e2e():
    for q in QUESTIONS:
        print(f'\n[질문] {q}')
        result = run_customs_agent(q)
        answer = result.get('final_response', '')
        print(f'[답변] {answer}')
        assert answer, 'final_response가 비어있음!'

if __name__ == '__main__':
    test_langgraph_e2e()
    print('\n테스트 완료!') 