from qdrant_client import QdrantClient
from google import genai

from config.config import config, GEMINI_API_KEY

genai_client = genai.Client(api_key=GEMINI_API_KEY)

qdrant_client = QdrantClient(host=config["qdrant"]["host"], port=config["qdrant"]["port"])
collection_name = config["qdrant"]["collection"]
embed_model = config["embedding"]["model"]
top_k = config["retrieval"]["top_k"]
top_p = config["retrieval"].get("top_p")

def retrieve_chunks(query: str) -> list:
    """ Embed query and retrieve top_k chunks from Qdrant collection
    
    Args:
        query (str): The query to embed
        
    Returns:
        list: A list of retrieved chunks
    """
    response = genai_client.models.embed_content(
        model=embed_model,
        contents=query
    )
    query_vector = response.embeddings[0].values
    
    search_kwargs = {
        "collection_name": collection_name,
        "query_vector": query_vector,
        "limit": top_k
    }
    
    if top_p is not None:
        search_kwargs["score_threshold"] = top_p
        
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        score_threshold=top_p
    )    
    chunks = []
    for point in search_result.points:
        chunks.append(point.payload)
    
    return chunks
