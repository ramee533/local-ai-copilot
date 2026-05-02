import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# Initialize Chroma client
client = chromadb.Client()

# Use Ollama embeddings (fast + no torch issues)
embedding_function = OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="nomic-embed-text"
)

# Create collection
collection = client.get_or_create_collection(
    name="de_docs",
    embedding_function=embedding_function
)

# ---------------------------
# ADD DOCUMENTS
# ---------------------------
def add_docs(chunks):
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"id_{i}_{hash(chunk)}"]
        )

# ---------------------------
# SEARCH DOCUMENTS
# ---------------------------
def search_docs(query):
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    if results and "documents" in results:
        return "\n".join(results["documents"][0])

    return ""