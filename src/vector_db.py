# src/vector_db.py
import os
import chromadb

# Define where ChromaDB will store its data files locally
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".chroma")
STYLE_GUIDE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "style_guide.txt")

# Initialize a Persistent Client (saves data directly to your disk)
chroma_client = chromadb.PersistentClient(path=DB_PATH)

def initialize_database():
    """
    Reads the style guide file, creates a collection, and indexes the rules.
    """
    # Create or fetch the collection. ChromaDB handles embeddings automatically.
    collection = chroma_client.get_or_create_collection(name="coding_guidelines")
    
    # Check if we already have documents indexed to avoid duplicating entries
    if collection.count() > 0:
        print(f"Database already initialized with {collection.count()} rules.")
        return collection

    if not os.path.exists(STYLE_GUIDE_PATH):
        print(f"Error: Could not find style guide at {STYLE_GUIDE_PATH}. Please create it first.")
        return collection

    print("Indexing style guide rules into Vector Database...")
    
    # Read the style guide rules line-by-line
    with open(STYLE_GUIDE_PATH, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    # Generate unique IDs for each rule chunk
    ids = [f"rule_{i}" for i in range(len(lines))]
    
    # Add the rules to our local database
    collection.add(
        documents=lines,
        ids=ids
    )
    print(f"Successfully indexed {len(lines)} rules into ChromaDB.")
    return collection

def query_relevant_rules(user_code, n_results=2):
    """
    Searches the database for rules semantically closest to the submitted code snippet.
    """
    collection = chroma_client.get_or_create_collection(name="coding_guidelines")
    
    # Run the vector similarity search
    results = collection.query(
        query_texts=[user_code],
        n_results=n_results
    )
    
    # Flatten out and extract the matching rule text strings
    retrieved_documents = results.get('documents', [[]])[0]
    return "\n".join(retrieved_documents)

# Local test block to ensure everything functions perfectly
if __name__ == "__main__":
    # Initialize and fill database
    initialize_database()
    
    # Test a mockup query
    test_query = "def handle_data(x): except: pass"
    print("\nSimulating a RAG search for a generic exception block...")
    matched_rules = query_relevant_rules(test_query)
    print("--- Matched Rules From Database ---")
    print(matched_rules)