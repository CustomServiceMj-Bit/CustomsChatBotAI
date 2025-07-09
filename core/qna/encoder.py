"""
Text encoding utilities using KoSimCSE-roberta model
"""
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from config import MODEL_NAME, DEVICE


class TextEncoder:
    def __init__(self):
        self.model = AutoModel.from_pretrained(MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model.to(DEVICE)
        
    def encode(self, sentences):
        """
        Encode sentences to embeddings using KoSimCSE model
        
        Args:
            sentences: str or list of str
            
        Returns:
            numpy.ndarray: L2 normalized embeddings
        """
        if isinstance(sentences, str):
            sentences = [sentences]
            
        self.model.eval()
        inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        
        with torch.no_grad():
            embeddings, *_ = self.model(**inputs, return_dict=False)
            cls_embeds = embeddings[:, 0, :]  # [CLS] token
            cls_embeds = cls_embeds.cpu().numpy()
            cls_embeds = cls_embeds / np.linalg.norm(cls_embeds, axis=1, keepdims=True)  # L2 normalization
            
        return cls_embeds


def cosine_score(a, b):
    """
    Calculate cosine similarity score between two tensors
    
    Args:
        a, b: torch.Tensor
        
    Returns:
        float: cosine similarity score (0-100)
    """
    if len(a.shape) == 1: 
        a = a.unsqueeze(0)
    if len(b.shape) == 1: 
        b = b.unsqueeze(0)
        
    a_norm = a / a.norm(dim=1, keepdim=True)
    b_norm = b / b.norm(dim=1, keepdim=True)
    
    return torch.mm(a_norm, b_norm.transpose(0, 1)).item() * 100