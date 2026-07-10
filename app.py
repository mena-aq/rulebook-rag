import streamlit as st
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

from rag.query_rewriter import rewrite_query
from rag.retriever import retrieve_chunks
from rag.answer_generator import generate_answer
from config.config import config

st.set_page_config(page_title="Student Rulebook QA", layout="wide")

project_root = Path(__file__).resolve().parent
pdf_path = project_root / config["paths"]["pdf"]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "pages_to_render" not in st.session_state:
    st.session_state.pages_to_render = [1]

# Main layout: Chat + PDF viewer side by side
col1, col2 = st.columns([1, 1], gap="large")

# ============ COLUMN 1: Chat Interface ============
with col1:
    st.title("Student Rulebook Chat")
    
    # Chat display area
    chat_container = st.container(height=500, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about attendance, grading, academic integrity..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Searching rulebook..."):
                    try:
                        # Build chat history for context (optional)
                        chat_history = [
                            {"role": m["role"], "content": m["content"]} 
                            for m in st.session_state.messages[:-1]
                        ]
                        
                        # Query pipeline
                        standalone_query = rewrite_query(chat_history, prompt)
                        retrieved_chunks = retrieve_chunks(standalone_query)
                        answer = generate_answer(prompt, retrieved_chunks)
                        
                        # Extract page references
                        relevant_pages = set()
                        for chunk in retrieved_chunks:
                            if 'page_start' in chunk and chunk['page_start']:
                                p_start = chunk['page_start']
                                p_end = chunk.get('page_end', p_start)
                                if p_end is None:
                                    p_end = p_start
                                for p in range(p_start, p_end + 1):
                                    relevant_pages.add(p) # 1-indexed
                        
                        if relevant_pages:
                            st.session_state.pages_to_render = sorted(list(relevant_pages))
                            st.session_state.current_page = st.session_state.pages_to_render[0]
                        
                        # Display answer
                        st.markdown(answer)
                        
                        # Show source pages
                        if retrieved_chunks:
                            with st.expander("📖 Sources"):
                                for i, chunk in enumerate(retrieved_chunks[:3], 1):
                                    page = chunk.get('page_start', 'N/A')
                                    st.caption(f"**Source {i}:** Page {page}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.caption("Make sure Qdrant is running and the PDF is ingested.")

# ============ COLUMN 2: PDF Viewer ============
with col2:
    st.subheader("📄 Document Viewer")
    
    if not pdf_path.exists():
        st.error(f"PDF not found at {pdf_path}")
    else:
        try:
            # Use streamlit-pdf-viewer
            pdf_viewer(
                str(pdf_path),
                width=420,
                height=650,
                render_text=True,
                pages_to_render=st.session_state.pages_to_render,
                key=f"pdf_viewer_{st.session_state.pages_to_render}"
            )
            
            # Page navigation
            st.divider()
            col_prev, col_page, col_next = st.columns(3)
            with col_prev:
                if st.button("⬅️ Prev", use_container_width=True):
                    if st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                        st.session_state.pages_to_render = [st.session_state.current_page]
                        st.rerun()
            
            with col_page:
                page_input = st.number_input(
                    "Go to page:",
                    min_value=1,
                    max_value=500,
                    value=st.session_state.current_page,
                    key="page_input"
                )
                if page_input != st.session_state.current_page:
                    st.session_state.current_page = page_input
                    st.session_state.pages_to_render = [st.session_state.current_page]
                    st.rerun()
            
            with col_next:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.current_page += 1
                    st.session_state.pages_to_render = [st.session_state.current_page]
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error loading PDF: {e}")
            st.caption("Try refreshing the page or checking the PDF file.")

# ============ Sidebar: Settings ============
with st.sidebar:
    st.header("⚙️ Settings")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.current_page = 1
        st.session_state.pages_to_render = [1]
        st.rerun()
    
    st.divider()
    st.caption(f"📄 **PDF:** {pdf_path.name if pdf_path.exists() else 'Not found'}")