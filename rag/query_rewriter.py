from groq import Groq

from utils.prompt_loader import load_prompt
from config.config import GROQ_API_KEY, config

client = Groq(api_key=GROQ_API_KEY)
temperature = config["llm"]["groq"]["temperature"]
llm_model = config["llm"]["groq"]["model"]


def rewrite_query(chat_history: list, question: str) -> str:
    """ Rewrites user questions into standalone search queries based on chat history
    
    Args:
        chat_history (list): The chat history
        question (str): The user question
        
    Returns:
        str: The rewritten question
    """
    if not chat_history:
        return question
        
    prompt_template = load_prompt("query_rewriter")
    
    history_str = ""
    for msg in chat_history:
        history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
    prompt = prompt_template.format(chat_history=history_str, question=question)
    
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
    
    standalone_query = response.choices[0].message.content.strip().replace("Standalone Query:", "").strip()
    return standalone_query
