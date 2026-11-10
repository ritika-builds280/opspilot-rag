import streamlit as st
from pypdf import PdfReader
from io import BytesIO
from dotenv import load_dotenv
from google import genai
import chromadb
import os
import hashlib
import time

# Streamlit interface
st.set_page_config(
    page_title="OpsPilot",
    page_icon="🤖",
    layout="wide"
)


# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Check your .env file.")
    st.stop()

# Connect to Gemini
gemini_client = genai.Client(api_key=api_key)

# Connect to persistent ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
   name="opspilot_documents_v2"
)

# Display processed documents
st.subheader("Processed Documents")

stored_documents = collection.get(
    include=["metadatas"]
)

if stored_documents["metadatas"]:
    document_names = sorted(set(
        item["filename"]
        for item in stored_documents["metadatas"]
    ))

    for document_name in document_names:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"📄 {document_name}")

        with col2:
            if st.button("Delete", key=f"delete_{document_name}"):
                collection.delete(
                    where={"filename": document_name}
                )
                st.success(f"{document_name} deleted successfully.")
                st.rerun()

else:
    st.info("No documents have been processed yet.")
# Split text into chunks
def split_into_chunks(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


# Generate embeddings
def generate_embeddings(texts, task_type):
    response = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config={"task_type": task_type}
    )

    return [
        item.values
        for item in response.embeddings
    ]



# Generate answer using retrieved context and conversation history
def generate_answer(question, context, chat_history=""):

    prompt = f"""
You are OpsPilot, an IT knowledge assistant.

Your responsibility is to provide accurate answers based
only on the uploaded IT documentation.

IMPORTANT RULES:

1. Use ONLY the provided documentation to answer questions.
2. Do not use your general knowledge to fill gaps in the documentation.
3. Distinguish between a topic being mentioned and a procedure
   being fully documented.
4. If a topic is mentioned but the actual steps or instructions
   are missing, clearly explain that the procedure is not documented.
5. Never invent commands, technical steps, configurations,
   recommendations, or troubleshooting instructions.
6. If the documentation explicitly mentions an approval requirement
   or safety restriction, include it in your answer.
7. If the documentation does not contain relevant information,
   state that the information is unavailable in the uploaded documents.
8. Use conversation history only to understand follow-up questions.
   Always base technical answers on the provided documentation.
9. Give clear, beginner-friendly answers.

Previous Conversation:
{chat_history}

Documentation:
{context}

Current Question:
{question}

Answer:
"""

    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if not response.text:
                return "I couldn't generate an answer. Please try again."

            return response.text

        except Exception as error:
            error_message = str(error)
            print("Gemini API Error:", error_message)

            if "503" in error_message or "UNAVAILABLE" in error_message:
                if attempt < 2:
                    wait_time = 2 ** (attempt + 1)
                    print(f"Retrying Gemini request in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                return (
                    "Gemini service is temporarily unavailable after "
                    "multiple attempts. Please try again later."
                )

            elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                return (
                    "Gemini API quota exceeded. "
                    "Please try again after your API quota resets."
                )

            else:
                return (
                    "Unable to generate an answer due to an API error. "
                    "Please try again later."
                )



st.title("🤖 OpsPilot - IT Knowledge Assistant")

st.write(
    "Upload IT documentation and ask questions "
    "to get answers based on your documents."
)

# Store conversation history during the current session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# PDF upload
st.subheader("1. Upload IT Documentation")

uploaded_files = st.file_uploader(
    "Choose PDF documents",
    type=["pdf"],
    accept_multiple_files=True
)
if uploaded_files:
    for uploaded_file in uploaded_files:

        if st.button(
            f"Process {uploaded_file.name}",
            key=uploaded_file.name
        ):
            try:
                pdf_bytes = uploaded_file.getvalue()

                file_hash = hashlib.sha256(pdf_bytes).hexdigest()

                existing_document = collection.get(
                    where={"file_hash": file_hash}
                )

                if existing_document["ids"]:
                    st.info(
                        f"{uploaded_file.name} has already been processed."
                    )
                    continue

                pdf_reader = PdfReader(
                    BytesIO(pdf_bytes)
                )
                all_chunks = []

                for page_number, page in enumerate(
                    pdf_reader.pages, start=1
                ):
                    page_text = page.extract_text() or ""

                    page_chunks = split_into_chunks(page_text)

                    for chunk_number, chunk in enumerate(
                        page_chunks, start=1
                    ):
                        all_chunks.append({
                            "text": chunk,
                            "page": page_number,
                            "chunk": chunk_number
                        })

                if not all_chunks:
                    st.warning("No readable text found in this PDF.")
                    continue

                texts = [
                    item["text"] for item in all_chunks
                ]

                with st.spinner("Generating embeddings..."):
                    embeddings = generate_embeddings(
                        texts,
                        "RETRIEVAL_DOCUMENT"
                    )

                document_ids = [
                    f"{uploaded_file.name}_page_{item['page']}_chunk_{item['chunk']}"
                    for item in all_chunks
                ]

                metadatas = [
                    {
                        "filename": uploaded_file.name,
                        "page": item["page"],
                        "chunk": item["chunk"],
                        "file_hash": file_hash
                    }
                    for item in all_chunks
                ]

                # Remove older version of the same document
                collection.delete(
                    where={"filename": uploaded_file.name}
                )

                collection.upsert(
                    ids=document_ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                st.success(
                    f"Successfully stored {len(texts)} chunks "
                    f"from {uploaded_file.name}!"
                )

            except Exception as error:
                st.error(f"PDF processing failed: {error}")


# Ask questions
st.divider()

st.subheader("2. Ask OpsPilot")

question = st.text_input(
    "Enter your question about the uploaded documentation:"
)



if st.button("Get Answer"):

    if not question.strip():
        st.warning("Please enter a question.")

    elif collection.count() == 0:
        st.warning("Please upload and process a PDF first.")

    else:
        try:
           
            with st.spinner("Searching documentation..."):

                if st.session_state.chat_history:
                    previous_question = st.session_state.chat_history[-1]["question"]

                    retrieval_query = (
                        f"Previous question: {previous_question}\n"
                        f"Current follow-up: {question}"
                    )
                else:
                    retrieval_query = question

                query_embedding = generate_embeddings(
                    [retrieval_query],
                    "RETRIEVAL_QUERY"
                )[0]


                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(3, collection.count()),
                    include=["documents", "metadatas", "distances"]
                )

                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]

                threshold = 0.70

                relevant_results = [
                    (doc, metadata, distance)
                    for doc, metadata, distance in zip(
                        documents, metadatas, distances
                    )
                    if distance <= threshold
                ]

            if not relevant_results:
                st.warning(
                    "The uploaded documentation does not contain "
                    "sufficiently relevant information to answer "
                    "this question."
                )

           
            else:
                context = "\n\n".join(
                    doc for doc, metadata, distance in relevant_results
                )

                chat_history_text = "\n".join(
                    [
                        f"User: {item['question']}\nAssistant: {item['answer']}"
                        for item in st.session_state.chat_history
                    ]
                )

                with st.spinner("Generating answer..."):
                    answer = generate_answer(
                        question,
                        context,
                        chat_history_text
                    )

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer
                })

                st.subheader("OpsPilot Answer")
                st.write(answer)

                st.subheader("Sources")

                displayed_sources = set()

                for doc, metadata, distance in relevant_results:
                    filename = metadata.get("filename", "Unknown")
                    page = metadata.get("page", "Not recorded")

                    source_key = (filename, page)

                    if source_key not in displayed_sources:
                        st.write(
                            f"- {filename} (Page {page})"
                        )
                        displayed_sources.add(source_key)


        except Exception as error:
            st.error(f"Unable to generate answer: {error}")

if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()

st.subheader("Conversation History")

for item in st.session_state.chat_history:
    st.markdown(f"**You:** {item['question']}")
    st.markdown(f"**OpsPilot:** {item['answer']}")
    st.divider()

st.divider()

st.caption(
    "OpsPilot | AI-powered IT Knowledge Assistant"
)