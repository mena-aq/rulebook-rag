from pathlib import Path
import os

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)  # dictionary with keys

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GEMINI_API_KEY or not GROQ_API_KEY:
    raise ValueError("GEMINI_API_KEY or GROQ_API_KEY not found in .env")