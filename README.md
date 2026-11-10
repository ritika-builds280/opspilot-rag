\# OpsPilot – AI-Powered IT Knowledge Assistant



\## 1. Project Overview



OpsPilot is a Retrieval-Augmented Generation (RAG) application designed to help IT teams retrieve information from technical documentation and Standard Operating Procedures (SOPs).



Users can upload PDF documents and ask questions in natural language. OpsPilot retrieves relevant document sections using semantic search and uses Google's Gemini model to generate answers grounded in the retrieved content.



The application also displays source document names and page references to help users verify the information.



\## 2. Problem Statement



IT teams frequently work with technical documentation, troubleshooting guides and operational procedures. Finding specific information across multiple documents can be time-consuming.



OpsPilot aims to simplify this process through document-based semantic search and AI-powered question answering.



\## 3. Key Features



\- Multiple PDF document uploads.

\- PDF text extraction using PyPDF.

\- Text chunking with configurable chunk size and overlap.

\- Semantic embeddings using Google's Gemini embedding model.

\- Persistent vector storage using ChromaDB.

\- Similarity-based document retrieval.

\- Context-grounded answer generation using Gemini.

\- Source references with document names and page numbers.

\- Relevance threshold for filtering retrieved content.

\- Fallback response for unsupported questions.

\- Conversation history and contextual follow-up questions.

\- Clear conversation functionality.

\- Duplicate document detection using SHA-256 hashing.

\- Updated document replacement.

\- Processed document listing and deletion.

\- API error handling for quota and service availability issues.

\- Retrieval evaluation using a separate test set.



\## 4. Technology Stack



| Technology | Purpose |

|---|---|

| Python | Application development |

| Streamlit | User interface |

| Google Gemini | Answer generation |

| Gemini Embedding API | Text embeddings |

| ChromaDB | Vector database |

| PyPDF | PDF text extraction |

| python-dotenv | Environment variable management |



\## 5. Architecture



The application follows a Retrieval-Augmented Generation architecture.



\### Document ingestion



1\. User uploads PDF documents.

2\. PyPDF extracts text from the documents.

3\. Extracted text is divided into smaller overlapping chunks.

4\. Gemini generates embeddings for the chunks.

5\. ChromaDB stores the embeddings, text and source metadata.



\### Question answering



1\. User submits a natural-language question.

2\. Gemini generates an embedding for the question.

3\. ChromaDB performs semantic similarity search.

4\. Relevant document chunks are retrieved.

5\. Retrieved context is passed to Gemini.

6\. Gemini generates a document-grounded answer.

7\. OpsPilot displays the answer and source references.



\### Architecture Diagram



```mermaid

flowchart TD

&#x20;   A\[User uploads PDF] --> B\[PyPDF Text Extraction]

&#x20;   B --> C\[Text Chunking]

&#x20;   C --> D\[Gemini Embedding Model]

&#x20;   D --> E\[(ChromaDB Vector Database)]



&#x20;   F\[User asks a question] --> G\[Question Embedding]

&#x20;   G --> H\[Semantic Similarity Search]

&#x20;   E --> H

&#x20;   H --> I\[Relevant Document Chunks]

&#x20;   I --> J\[Context Assembly]

&#x20;   J --> K\[Gemini LLM]

&#x20;   L\[Conversation History] --> K

&#x20;   K --> M\[Generated Answer]

&#x20;   I --> N\[Source References]

&#x20;   M --> O\[Streamlit Interface]

&#x20;   N --> O

```



\## 6. Project Workflow



PDF Upload → Text Extraction → Chunking → Embedding Generation → ChromaDB Storage → Semantic Retrieval → Context Assembly → Gemini Answer Generation → Source Display



\## 7. Installation and Setup



\### Prerequisites



\- Python

\- Google Gemini API key

\- Git



\### Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd opspilot-rag

```



\### Create a virtual environment



```bash

python -m venv .venv

```



\### Activate the environment



Windows Command Prompt:



```cmd

.venv\\Scripts\\activate.bat

```



\### Install dependencies



```bash

pip install -r requirements.txt

```



\### Configure the API key



Create a `.env` file in the project root:



```text

GEMINI\_API\_KEY=your\_api\_key\_here

```



Never commit the `.env` file or expose your API key.



\### Run the application



```bash

streamlit run app.py

```



Open the local Streamlit address displayed in the terminal.



\## 8. Evaluation and Testing



OpsPilot includes a separate retrieval evaluation script.



The evaluation test set covers:



\- Direct questions.

\- Specific technical questions.

\- Questions with different wording.

\- Out-of-scope questions.

\- Questions involving missing procedures.



Run the retrieval evaluation:



```bash

python evaluate\_retrieval.py

```



The evaluation script uses the Gemini embedding API to generate query embeddings and searches the persistent ChromaDB collection.



Initial testing demonstrated relevant retrieval for disk-space questions and higher distances for an unrelated VPN question.



The relevance threshold is provisional and requires further validation across additional documents and questions.



\## 9. Error Handling and Limitations



\- Gemini API quota limits may affect answer generation.

\- Temporary Gemini service outages may prevent responses.

\- Retrieval quality depends on document quality and chunking.

\- Scanned PDFs may require OCR support.

\- A topic mentioned in a document does not necessarily mean its full procedure is documented.

\- The application requires further testing before production use.



\## 10. Future Enhancements



\- Improved document-grounded answer validation.

\- Expanded retrieval evaluation and quality metrics.

\- Support for additional document formats.

\- OCR for scanned documents.

\- Improved conversational interface.

\- More robust API retry and recovery mechanisms.

\- Deployment and persistent hosted storage.

\- Enhanced multi-document retrieval.



\## 11. Project Status



This is a personal GenAI learning and portfolio project demonstrating practical implementation of Retrieval-Augmented Generation using Python, Gemini, ChromaDB and Streamlit.



It is intended for learning and demonstration purposes, not as a production IT operations system.



\## 12. Author



Developed as a personal Generative AI portfolio project.

