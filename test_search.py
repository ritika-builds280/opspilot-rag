from dotenv import load_dotenv
from google import genai
import chromadb
import os

# Load the API key
load_dotenv()

# Connect to Gemini
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Connect to the existing ChromaDB database
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="opspilot_documents_v2"
)

# Ask a question
question = "How can I check available disk space on Windows?"

# Convert the question into an embedding
response = gemini_client.models.embed_content(
    model="gemini-embedding-001",
    contents=question,
    config={
        "task_type": "RETRIEVAL_QUERY"
    }
)

query_embedding = response.embeddings[0].values

# Search for the two most relevant chunks
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

# Display search results
print("\nQuestion:", question)
print("\nRelevant document chunks:\n")
for chunk_id, document, distance in zip(
    results["ids"][0],
    results["documents"][0],
    results["distances"][0]
):
    print(f"\nChunk ID: {chunk_id}")
    print(f"Distance: {distance:.3f}")
    print(document)
    print("-------------------------")