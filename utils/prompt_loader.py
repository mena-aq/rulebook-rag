from pathlib import Path

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the prompts directory.

    Args:
        prompt_name (str): The name of the prompt to load (without .md extension)
        
    Returns:
        str: The content of the prompt
    """
    project_root = Path(__file__).resolve().parent.parent
    prompt_path = project_root / "prompts" / f"{prompt_name}.md"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
