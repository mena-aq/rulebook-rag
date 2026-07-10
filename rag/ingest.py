import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import os
import re
import fitz  # PyMuPDF
import tiktoken
from tqdm import tqdm
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from utils.logger import get_logger
from config.config import config
from config.config import GEMINI_API_KEY

logger = get_logger(__name__)

def is_title_page(page_num, text):
    """
    Check if a page is the title page.
    """
    if page_num == 0:
        return True
    return False

def is_toc_page(text):
    """
    Check if a page is the table of contents.
    """
    if "table of contents" in text[:500].lower():
        return True
    if text.count("...") > 20:
        return True
    return False

def count_tokens(text: str) -> int:
    """ 
    Count the number of tokens in a text.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def chunk_text(text: str, max_tokens: int, overlap_tokens: int):
    """
    Chunks text into fixed size token windows with overlap.
    
    Args:
        text: The text to chunk.
        max_tokens: The maximum number of tokens per chunk.
        overlap_tokens: The number of tokens to overlap between chunks.
        
    Returns:
        A list of chunks.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    
    chunks = []
    if len(tokens) == 0:
        return chunks
        
    step = max_tokens - overlap_tokens
    if step <= 0:
        step = max_tokens
        
    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_str = enc.decode(chunk_tokens).strip()
        if chunk_str:
            chunks.append(chunk_str)
        
    return chunks

def extract_document_text(pdf_path: str):
    """
    Extracts continuous text from a PDF document and maintains a page mapping.
    
    Args:
        pdf_path: The path to the PDF document.
        
    Returns:
        A tuple of (continuous_text, page_mapping)
    """
    doc = fitz.open(pdf_path)
    
    current_text = ""
    page_mapping = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_blocks = page.get_text("dict")["blocks"]
        
        raw_text = page.get_text("text")
        if not raw_text.strip():
            logger.info(f"Skipping page {page_num + 1}: Blank page.")
            continue
        if is_title_page(page_num, raw_text):
            logger.info(f"Skipping page {page_num + 1}: Title page.")
            continue
        if is_toc_page(raw_text):
            logger.info(f"Skipping page {page_num + 1}: Table of Contents.")
            continue
            
        page_start_idx = len(current_text)
        page_has_text = False
        
        for block in text_blocks:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                            
                        # Skip footers and headers based on heuristics
                        upper_text = text.upper()
                        if (
                            "ACADEMIC RULES" in upper_text or 
                            "NATIONAL UNIVERSITY" in upper_text or 
                            (text.isdigit() and len(text) < 4)
                        ):
                            continue
                            
                        if current_text:
                            current_text += " " + text
                        else:
                            current_text = text
                            
                        page_has_text = True
                        
        if page_has_text:
            end_idx = len(current_text)
            page_mapping.append({"page_num": page_num + 1, "start": page_start_idx, "end": end_idx})
            
    return current_text, page_mapping


def ingest():
    """
    Ingests the PDF document into the Qdrant database.
    """
    pdf_path = project_root / config["paths"]["pdf"]
    if not pdf_path.exists():
        logger.error(f"PDF not found at {pdf_path}")
        return

    logger.info("Extracting document text...")
    text, page_mapping = extract_document_text(str(pdf_path))
    
    max_tokens = config["chunking"]["max_tokens"]
    overlap_tokens = config["chunking"]["overlap_tokens"]
    
    logger.info("Chunking text...")
    chunks = chunk_text(text, max_tokens, overlap_tokens)
    
    final_chunks = []
    chunk_id = 1
    
    search_start_idx = 0
    for chunk in chunks:
        # Find exact character indices for page mapping
        search_chunk = chunk[:50]
        chunk_start = text.find(search_chunk, search_start_idx)
        if chunk_start == -1:
            chunk_start = search_start_idx
            
        chunk_end = chunk_start + len(chunk)
        
        page_start = None
        page_end = None
        
        for mapping in page_mapping:
            if mapping["start"] <= chunk_end and mapping["end"] >= chunk_start:
                if page_start is None:
                    page_start = mapping["page_num"]
                page_end = mapping["page_num"]
                
        if page_start is None:
            page_start = page_mapping[0]["page_num"] if page_mapping else 1
        if page_end is None:
            page_end = page_mapping[-1]["page_num"] if page_mapping else 1
            
        final_chunks.append({
            "id": f"chunk_{chunk_id:04d}",
            "document": pdf_path.name,
            "page_start": page_start,
            "page_end": page_end,
            "text": chunk
        })
        chunk_id += 1
        search_start_idx = chunk_start + (len(chunk) // 2)
            
    logger.info(f"Generated {len(final_chunks)} chunks.")
    
    logger.info("Generating embeddings and indexing to Qdrant...")
    
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    qdrant_client = QdrantClient(host=config["qdrant"]["host"], port=config["qdrant"]["port"])
    collection_name = config["qdrant"]["collection"]
    embed_model = config["embedding"]["model"]

    if not final_chunks:
        logger.warning("No chunks to ingest.")
        return
        
    try:
        response = genai_client.models.embed_content(
            model=embed_model,
            contents=final_chunks[0]["text"]
        )
        first_embedding = response.embeddings[0].values
        vector_size = len(first_embedding)
    except Exception as e:
        logger.error(f"Error testing embedding model: {e}")
        return
        
    
    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)
        
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    
    points = []
    
    has_error = False
    for i, chunk_data in enumerate(tqdm(final_chunks)):
        try:
            if i == 0:
                embedding = first_embedding
            else:
                response = genai_client.models.embed_content(
                    model=embed_model,
                    contents=chunk_data["text"]
                )
                embedding = response.embeddings[0].values

            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "id": chunk_data["id"],
                    "document": chunk_data["document"],
                    "page_start": chunk_data["page_start"],
                    "page_end": chunk_data["page_end"],
                    "text": chunk_data["text"]
                }
            )
            points.append(point)
            
            if len(points) >= 100:
                qdrant_client.upsert(collection_name=collection_name, points=points)
                points = []
        except Exception as e:
            logger.error(f"Error embedding chunk {chunk_data['id']}: {e}")
            has_error = True
            break
            
    if has_error:
        logger.error("Ingestion failed due to embedding errors. Aborting.")
        return
        
    if points:
        qdrant_client.upsert(collection_name=collection_name, points=points)
        
    logger.info("Ingestion complete!")


if __name__ == "__main__":
    ingest()
