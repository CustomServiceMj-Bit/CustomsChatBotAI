from flask import Flask, jsonify
from flasgger import Swagger
from .routes import api_blueprint

def create_app():
    app = Flask(__name__)
    Swagger(app)
    app.register_blueprint(api_blueprint)
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "관세청 챗봇 API 서버",
            "endpoints": {
                "/predict": "POST - 관세 예측 및 통관 관련 질문 처리",
                "/apidocs": "GET - API 문서 (Swagger)"
            },
            "example": {
                "question": "미국에서 150만원에 노트북을 샀는데 관세가 얼마나 나올까요?"
            }
        })
    
    return app