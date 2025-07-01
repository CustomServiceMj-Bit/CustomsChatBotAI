from flask import Blueprint, request, jsonify
from flasgger import swag_from
from .service import run_model

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
                    }
                }
            }
        }
    }
})
def predict():
    question = request.json.get("question")
    answer = run_model(question=question)
    return jsonify({"answer": answer})