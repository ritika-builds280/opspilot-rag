from dotenv import load_dotenv
from google import genai
import chromadb
import os

load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="opspilot_documents"
)

# User's question
question = "How can I check available disk space on Windows?"

# Generate an embedding for the question
response = gemini_client.models.embed_content(
    model="gemini-embedding-001",
    contents=question,
    config={
        "task_type": "RETRIEVAL_QUERY"
    }
)

query_embedding = response.embeddings[0].values

# Retrieve relevant document chunks
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

context = "\n\n".join(results["documents"][0])

# Ask Gemini to generate an answer using retrieved context
prompt = f"""
You are OpsPilot, an IT knowledge assistant.

Answer the question using ONLY the information in the
provided documentation.

If the documentation does not contain the answer,
say that the information is not available in the
uploaded documents.

Documentation:
{context}

Question:
{question}

Provide a clear, beginner-friendly answer.
"""

answer = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt
)

print("\nQuestion:", question)
print("\nOpsPilot Answer:\n")
print(answer.text)