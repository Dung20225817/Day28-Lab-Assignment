# scripts/05_embed_to_qdrant.py
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

EMBED_URL = os.environ.get("EMBED_NGROK_URL", "")
qdrant = QdrantClient(host="localhost", port=6333)

# Tao collection
try:
    qdrant.delete_collection(collection_name="documents")
except:
    pass
qdrant.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

def get_embeddings_local(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(texts).tolist()

def embed_and_store(records: list[dict]):
    # Goi Kaggle embedding service neu co, fallback local
    if EMBED_URL and EMBED_URL != "https://your-embed-url.ngrok-free.app":
        try:
            response = requests.post(f"{EMBED_URL}/embed", json={"texts": [r["text"] for r in records]}, timeout=10)
            embeddings = response.json()["embeddings"]
            print("Using Kaggle embedding service")
        except Exception:
            embeddings = get_embeddings_local([r["text"] for r in records])
            print("Using local embedding (Kaggle service unavailable)")
    else:
        embeddings = get_embeddings_local([r["text"] for r in records])
        print("Using local embedding (no Kaggle URL configured)")

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

# Test voi sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
