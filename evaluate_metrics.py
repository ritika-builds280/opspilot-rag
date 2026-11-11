import os
import chromadb
from dotenv import load_dotenv
from google import genai
from relevance_labels import relevance_tests

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found in .env file.")

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

precision_scores = []
recall_scores = []

for test in relevance_tests:
    question = test["question"]
    relevant_chunks = set(test["relevant_chunks"])

    query_embedding = generate_query_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    retrieved_ids = results["ids"][0]

    retrieved_chunks = {
        int(chunk_id.split("_")[-1])
        for chunk_id in retrieved_ids
    }

    relevant_retrieved = retrieved_chunks.intersection(relevant_chunks)

    print("\n" + "=" * 50)
    print(f"Question: {question}")
    print(f"Retrieved chunks: {sorted(retrieved_chunks)}")
    print(f"Relevant chunks: {sorted(relevant_chunks)}")

    if not relevant_chunks:
        best_distance = min(results["distances"][0])

        print("Test type: Out-of-scope question")
        print(f"Best distance: {best_distance:.3f}")
        print("Precision@3: N/A")
        print("Recall@3: N/A")

        if best_distance >= 0.75:
            print("Out-of-scope result: PASS")
        else:
            print("Out-of-scope result: REVIEW")

    else:
        precision = len(relevant_retrieved) / len(retrieved_chunks)
        recall = len(relevant_retrieved) / len(relevant_chunks)
        precision_scores.append(precision)
        recall_scores.append(recall)

        print(f"Relevant retrieved: {sorted(relevant_retrieved)}")
        print(f"Precision@3: {precision:.2%}")
        print(f"Recall@3: {recall:.2%}")
if precision_scores and recall_scores:
    print("\n" + "=" * 50)
    print("IN-SCOPE EVALUATION SUMMARY")

    average_precision = sum(precision_scores) / len(precision_scores)
    average_recall = sum(recall_scores) / len(recall_scores)

    print(f"Average Precision@3: {average_precision:.2%}")
    print(f"Average Recall@3: {average_recall:.2%}")    