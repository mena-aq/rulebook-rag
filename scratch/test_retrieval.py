import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from google import genai
from config.config import config, GEMINI_API_KEY

genai_client = genai.Client(api_key=GEMINI_API_KEY)
qdrant_client = QdrantClient(host=config["qdrant"]["host"], port=config["qdrant"]["port"])
collection_name = config["qdrant"]["collection"]
embed_model = config["embedding"]["model"]

query = "tell me about scholarships"

response = genai_client.models.embed_content(
    model=embed_model,
    contents=query
)
query_vector = response.embeddings[0].values

search_result = qdrant_client.query_points(
    collection_name=collection_name,
    query=query_vector,
    limit=5
)

print(f"Top chunks for query '{query}':")
for point in search_result.points:
    print(f"Score: {point.score:.4f} - {point.payload['text'][:100]}...")
