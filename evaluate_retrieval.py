import os
import chromadb
from dotenv import load_dotenv
from google import genai
from evaluation_questions import evaluation_tests

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("opspilot_documents_v2")


def generate_query_embedding(question):
    response = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config={"task_type": "RETRIEVAL_QUERY"}
    )

    return response.embeddings[0].values


for test in evaluation_tests:
    question = test["question"]

    print("\n" + "=" * 60)
    print(f"Test {test['id']}: {test['test_type']}")
    print(f"Question: {question}")

    query_embedding = generate_query_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(3, collection.count())
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for index, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        print(f"\nRetrieved result {index}")
        print(f"Distance: {distance:.3f}")
        print(
            f"Source: {metadata.get('filename')}, "
            f"Page {metadata.get('page')}"
        )
        print(f"Content: {document[:300]}")

print("\nEvaluation retrieval checks completed.")