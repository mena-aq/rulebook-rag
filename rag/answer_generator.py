import os
import groq

from utils.prompt_loader import load_prompt
from config.config import GROQ_API_KEY, config

client = groq.Groq(api_key=GROQ_API_KEY)
llm_model = config["llm"]["groq"]["model"]
temperature = config["llm"]["groq"]["temperature"]

def generate_answer(question: str, retrieved_chunks: list) -> str:
    """Generates an answer to the user's question based on the retrieved chunks
    
    Args:
        question (str): The user question
        retrieved_chunks (list): The retrieved chunks
        
    Returns:
        str: The generated answer
    """
    prompt_template = load_prompt("answer_generator")
    
    context_str = ""
    for i, chunk in enumerate(retrieved_chunks):
        page_start = chunk.get('page_start')
        page_end = chunk.get('page_end')
        
        page_str = f"Page {page_start}" if page_start == page_end else f"Pages {page_start}-{page_end}"
        context_str += f"--- {page_str} ---\n{chunk['text']}\n\n"
    
    prompt = prompt_template.format(context=context_str, question=question)
    
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=temperature,
    )
    
    return response.choices[0].message.content.strip()
