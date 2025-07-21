from flask import Blueprint, request, jsonify, make_response
from app.dto.request import Request
from flasgger import swag_from
from .service import run_model
import uuid

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/predict", methods=["POST"])
@swag_from({
    'tags': ['Prediction'],
    'parameters': [
        {
            'name': 'question',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'question': {
                        'type': 'string',
                        'example': '이 물건의 세금이 얼마나 나올까?'
                    },
                    'session_id': {
                        'type': 'string',
                        'example': 'uuid-1234',
                        'required': False
                    }
                },
                'required': ['question']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Predicted answer',
            'schema': {
                'type': 'object',
                'properties': {
                    'answer': {
                        'type': 'string',
                        'example': '이 물건은 8%의 부가세가 부과됩니다.'
                    },
                    'session_id': {
                        'type': 'string',
                        'example': 'uuid-1234'
                    }
                }
            }
        }
    }
})
def predict():
    request_data = Request(**request.get_json())
    session_id = request_data.session_id or request.cookies.get("session_id")
    answer = run_model(question=request_data.message, session_id=session_id)
    # 응답 dict에서 session_id 제거
    answer_dict = answer.model_dump()
    answer_dict.pop("session_id", None)
    response = make_response(jsonify(answer_dict))
    # 쿠키는 그대로 관리
    if answer.session_id:
        response.set_cookie("session_id", answer.session_id)
    else:
        response.delete_cookie("session_id")
    return response