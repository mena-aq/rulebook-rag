# Rulebook RAG

A RAG (Retrieval-Augmented Generation) application for querying the FAST-NUCES Student Rulebook. Ask natural language questions and get answers with page-level citations, displayed alongside a live PDF viewer.

## Requirements

- Python 3.12+
- Docker (for Qdrant)
    - version 1.18.2
- Groq API key


## Setup

1. **Start Qdrant:**

   ```bash
   docker compose up -d
   ```

2. **Install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   Create a `.env` file in the project root:

   ```
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Ingest the PDF:**

   ```bash
   python cli.py
   ```

5. **Run the app:**

   ```bash
   streamlit run app.py
   ```

## Demo

![Demo](assets/demo_image.png)
