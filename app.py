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


# Custom OpsPilot UI styling

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #172B4D;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #172B4D;
    }

    div.stButton > button {
        background-color: #244A78;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #3569A5;
        color: white;
    }

    /* Upload section */
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: #EAF2FC;
        border: 1.5px dashed #6B94C4;
        border-radius: 12px;
        padding: 14px;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] * {
        color: #172B4D !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] small {
        display: block !important;
        visibility: visible !important;
        color: #526B89 !important;
        font-size: 12px !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background-color: #244A78 !important;
        color: #FFFFFF !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] button * {
        color: #FFFFFF !important;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
    }

    [data-testid="stChatMessageContent"] {
        line-height: 1.7;
    }

    [data-testid="stChatInput"] {
        border-radius: 12px;
    }

    hr {
        border-color: #DCE3ED;
    }
</style>
""", unsafe_allow_html=True)


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

# Sidebar - Processed Documents
st.sidebar.title("📚 Knowledge Base")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    st.session_state.chat_history = []
    st.session_state.pop("suggested_question", None)
    st.rerun()

st.sidebar.subheader("Processed Documents")

stored_documents = collection.get(
    include=["metadatas"]
)

if stored_documents["metadatas"]:
    document_names = sorted(set(
        item["filename"]
        for item in stored_documents["metadatas"]
    ))

    st.sidebar.caption(
        f"{len(document_names)} document(s) available"
    )

    for document_name in document_names:
        with st.sidebar.container():
            st.sidebar.write(f"📄 {document_name}")

            if st.sidebar.button(
                "Delete",
                key=f"delete_{document_name}"
            ):
                collection.delete(
                    where={"filename": document_name}
                )
                st.sidebar.success(
                    f"{document_name} deleted successfully."
                )
                st.rerun()

else:
    st.sidebar.info("No documents uploaded yet.")
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
10. Do not add extra fields, examples, recording requirements,
    or procedural details unless they are explicitly supported
    by the provided documentation.
11. Clearly distinguish documented facts from information
    that is not available in the documentation.
12. Do not repeat the entire conversation history in your answer.

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
                model="gemini-3.5-flash-lite",
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



# Main application header
st.markdown("""
<div style="padding: 10px 0 25px 0;">
    <h1 style="font-size: 38px; margin-bottom: 5px;">
        🤖 OpsPilot
    </h1>
    <p style="font-size: 17px; color: #64748B;">
        Your AI-powered IT Knowledge Assistant
    </p>
    <p style="font-size: 14px; color: #64748B;">
        Ask questions, explore technical procedures, and find answers
        directly from your uploaded documentation.
    </p>
</div>
""", unsafe_allow_html=True)

# Store conversation history during the current session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# PDF upload

st.sidebar.subheader("Upload IT Documentation")

uploaded_files = st.sidebar.file_uploader(
    "Choose PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
    help="Maximum file size: 200MB per file. PDF format only."
)

if uploaded_files:
    for uploaded_file in uploaded_files:

        if st.sidebar.button(
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

                pdf_reader = PdfReader(BytesIO(pdf_bytes))
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

                texts = [item["text"] for item in all_chunks]

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

st.subheader("Chat with OpsPilot")


# Welcome screen when no conversation exists
if not st.session_state.chat_history:

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #FFFFFF, #EEF4FC);
        padding: 45px 30px;
        border-radius: 18px;
        text-align: center;
        border: 1px solid #DCE6F2;
        margin: 25px 0;
        box-shadow: 0 4px 15px rgba(23, 43, 77, 0.05);
    ">
        <div style="font-size: 52px; margin-bottom: 10px;">🤖</div>
        <h2 style="color: #172B4D; margin-bottom: 10px;">
            Welcome to OpsPilot!
        </h2>
        <p style="color: #475569; font-size: 17px;">
            Your intelligent IT Knowledge Assistant
        </p>
        <p style="color: #64748B; font-size: 15px;">
            Explore your IT documentation, find technical procedures,
            and get answers grounded in your uploaded SOPs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 💡 Try asking OpsPilot")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💾 Check available disk space",
            use_container_width=True
        ):
            st.session_state.suggested_question = (
                "How can I check available disk space?"
            )
            st.rerun()

    with col2:
        if st.button(
            "⚙️ Check Windows service status",
            use_container_width=True
        ):
            st.session_state.suggested_question = (
                "How can I check Windows service status?"
            )
            st.rerun()

# Display previous conversation messages
for item in st.session_state.chat_history:

    with st.chat_message("user"):
        st.markdown(item["question"])

    with st.chat_message("assistant"):
        st.markdown(item["answer"])

        sources = item.get("sources", [])

        if sources:
            with st.expander("📚 Source Documents"):
                for source in sources:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: white;
                            border: 1px solid #E2E8F0;
                            border-radius: 8px;
                            padding: 12px;
                            margin-bottom: 8px;
                        ">
                            <div style="font-weight: 600; color: #244A78;">
                                📄 {source['filename']}
                            </div>
                            <div style="font-size: 13px; color: #64748B;">
                                Page {source['page']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# Chat input
question = st.chat_input(
    "Ask a question about your uploaded IT documents..."
)

if st.session_state.get("suggested_question"):
    question = st.session_state.suggested_question
    del st.session_state.suggested_question

if question:

    if collection.count() == 0:
        answer = "Please upload and process a PDF first."
        sources = []

        st.session_state.chat_history.append({
            "question": question,
            "answer": answer,
            "sources": sources
        })

        st.rerun()

    else:
        try:
            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("Searching documentation..."):

                if st.session_state.chat_history:
                    previous_question = (
                        st.session_state.chat_history[-1]["question"]
                    )

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
                answer = (
                    "The uploaded documentation does not contain "
                    "sufficiently relevant information to answer "
                    "this question."
                )
                sources = []

            else:
                context = "\n\n".join(
                    doc for doc, metadata, distance in relevant_results
                )

                chat_history_text = "\n".join(
                    [
                        f"User: {item['question']}\n"
                        f"Assistant: {item['answer']}"
                        for item in st.session_state.chat_history
                    ]
                )

                with st.spinner("Generating answer..."):
                    answer = generate_answer(
                        question,
                        context,
                        chat_history_text
                    )

                sources = []
                displayed_sources = set()

                for doc, metadata, distance in relevant_results:
                    filename = metadata.get("filename", "Unknown")
                    page = metadata.get("page", "Not recorded")

                    source_key = (filename, page)

                    if source_key not in displayed_sources:
                        sources.append({
                            "filename": filename,
                            "page": page
                        })
                        displayed_sources.add(source_key)

            # Save conversation
            st.session_state.chat_history.append({
                "question": question,
                "answer": answer,
                "sources": sources
            })

            # Refresh to display the complete conversation
            st.rerun()

        except Exception as error:
            st.error(f"Unable to generate answer: {error}")


if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()



st.divider()

st.caption(
    "OpsPilot | AI-powered IT Knowledge Assistant"
)
