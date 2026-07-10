from rag.query_rewriter import rewrite_query
from rag.retriever import retrieve_chunks
from rag.answer_generator import generate_answer

def main():
    print("Welcome to the Student Rulebook RAG CLI!")
    print("Type 'exit' or 'quit' to close the application.\n")
    
    chat_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            # 1. Query Rewriting
            standalone_query = rewrite_query(chat_history, user_input)
            
            # 2. Retrieval
            retrieved_chunks = retrieve_chunks(standalone_query)
            
            # 3. Answer Generation
            answer = generate_answer(user_input, retrieved_chunks)
            
            print(f"\nRulebookBot: {answer}\n")
            
            # Update chat history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": answer})
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
