
import os
import chromadb
from dotenv import load_dotenv
from google import genai
from evaluation_questions import evaluation_tests

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


passed = 0
total = len(evaluation_tests)

for test in evaluation_tests:
    question = test["question"]
    expected_keywords = test["expected_keywords"]

    print("\n" + "=" * 60)
    print(f"Test {test['id']}: {test['test_type']}")
    print(f"Question: {question}")

    try:
        query_embedding = generate_query_embedding(question)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(3, collection.count())
        )

        documents = results["documents"][0]
        distances = results["distances"][0]

        retrieved_text = " ".join(documents).lower()

        if expected_keywords:
            matched_keywords = [
                keyword for keyword in expected_keywords
                if keyword.lower() in retrieved_text
            ]

            score = len(matched_keywords) / len(expected_keywords)
            test_passed = score >= 0.5

            print(f"Matched keywords: {matched_keywords}")
            print(f"Keyword coverage: {score:.0%}")

        else:
            best_distance = min(distances) if distances else float("inf")
            threshold = test.get("expected_max_distance", 0.75)
            test_passed = best_distance >= threshold

            print(f"Best distance: {best_distance:.3f}")
            print(f"Distance threshold: {threshold:.3f}")

        if test_passed:
            passed += 1
            print("Result: PASS")
        else:
            print("Result: FAIL")

    except Exception as error:
        print(f"Evaluation error: {error}")
        print("Result: ERROR")

print("\n" + "=" * 60)
print("RETRIEVAL EVALUATION SUMMARY")
print(f"Tests passed: {passed}/{total}")
print(f"Pass rate: {(passed / total) * 100:.1f}%")
print("Evaluation completed.")
