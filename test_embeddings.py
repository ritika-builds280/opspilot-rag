from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents="How do I check disk space on a Windows server?",
    config={
        "task_type": "RETRIEVAL_DOCUMENT"
    }
)

embedding = response.embeddings[0].values

print("Embedding generated successfully!")
print("Number of values:", len(embedding))
print("First five values:", embedding[:5])