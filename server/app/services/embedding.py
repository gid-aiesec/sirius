from sentence_transformers import SentenceTransformer

print("Loading SentenceTransformer model (all-mpnet-base-v2)...")
_model = SentenceTransformer('all-mpnet-base-v2')
print("Model loaded successfully!")

def embed_query(text: str) -> list[float]:
    vector = _model.encode(text).tolist()
    return vector