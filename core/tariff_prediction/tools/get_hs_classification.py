import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
from langchain_core.tools import tool
import os

# sentence_transformers 임포트 시도
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# MLP 클래스 정의
class MLP(nn.Module):
    def __init__(self, output_size):
        super(MLP, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(1024, 512), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, output_size)
        )
    def forward(self, x):
        return self.layers(x)

def load_model():
    """모델을 로드합니다."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None, None, None, None
    try:
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
        embedding_model_path = os.path.join(model_dir, 'bge-m3-custom-supervised')
        label_encoder_path = os.path.join(model_dir, 'label_encoder.pkl')
        mlp_model_path = os.path.join(model_dir, 'mlp_classifier.pth')
        if not all(os.path.exists(path) for path in [embedding_model_path, label_encoder_path, mlp_model_path]):
            return None, None, None, None
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        embedding_model = SentenceTransformer(embedding_model_path)
        label_encoder = joblib.load(label_encoder_path)
        output_size = len(label_encoder.classes_)
        classifier_model = MLP(output_size).to(device)
        classifier_model.load_state_dict(torch.load(mlp_model_path, map_location=device))
        classifier_model.eval()
        return embedding_model, label_encoder, classifier_model, device
    except Exception:
        return None, None, None, None

def predict_hs_code(item_description: str, embedding_model, label_encoder, classifier_model, device):
    if not all([embedding_model, label_encoder, classifier_model, device]):
        return []
    formatted_text = f"품명: {item_description} [SEP] 상세설명:"
    with torch.no_grad():
        embedding = embedding_model.encode(formatted_text, convert_to_tensor=True, normalize_embeddings=True)
        embedding = embedding.to(device).unsqueeze(0)
        logits = classifier_model(embedding)
        probabilities = torch.nn.functional.softmax(logits, dim=1)
        top5_prob, top5_indices = torch.topk(probabilities, 5)
    results = []
    top5_indices_cpu = top5_indices.cpu().numpy().flatten()
    top5_prob_cpu = top5_prob.cpu().numpy().flatten()
    predicted_hs_codes = label_encoder.inverse_transform(top5_indices_cpu)
    for code, prob in zip(predicted_hs_codes, top5_prob_cpu):
        results.append({"hs_code": code, "probability": f"{prob:.2%}"})
    return results

@tool
def get_hs_classification(product_name: str) -> str:
    """상품명으로 HS 코드를 예측합니다. 실제 ML 모델을 사용하여 정확한 HS 코드를 예측합니다."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return "HS 코드 예측 모델이 준비되어 있지 않습니다."
    embedding_model, label_encoder, classifier_model, device = load_model()
    if not all([embedding_model, label_encoder, classifier_model, device]):
        return "HS 코드 예측 모델이 준비되어 있지 않습니다."
    results = predict_hs_code(product_name, embedding_model, label_encoder, classifier_model, device)
    if not results:
        return "HS 코드 예측 결과가 없습니다."
    result_text = f"{product_name}의 예측된 HS 코드:\n"
    for i, result in enumerate(results[:3], 1):
        result_text += f"{i}. {result['hs_code']} (확률: {result['probability']})\n"
    return result_text 