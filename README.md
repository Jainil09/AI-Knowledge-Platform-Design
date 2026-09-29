# Enterprise AI Knowledge Platform — RAG Backend

A robust, production-ready backend platform for ingesting, processing, and querying enterprise knowledge using **Retrieval-Augmented Generation (RAG)**.

Built with **FastAPI**, the platform supports code files, plain text, Markdown, and complex PDFs. It includes asynchronous document processing and an automatic **OCR fallback** for scanned or image-based PDFs.

---

## 🚀 Features

### End-to-End RAG Pipeline

Automatically processes enterprise documents through the complete RAG pipeline:

```text
Document
   ↓
Text Extraction
   ↓
Chunking
   ↓
OpenAI Embeddings
   ↓
ChromaDB
   ↓
Semantic Search
   ↓
GPT-4o
   ↓
Context-Aware Answer
```

The system:

* Extracts text from uploaded documents
* Generates overlapping semantic chunks
* Creates vector embeddings using `text-embedding-3-small`
* Stores embeddings in a persistent ChromaDB database
* Retrieves relevant context using semantic similarity
* Generates answers using `gpt-4o`

---

### 📄 Self-Healing Document Ingestion

The platform uses **PyMuPDF** for fast PDF text extraction.

If a PDF does not contain a usable text layer, the system automatically falls back to **Tesseract OCR**.

```text
PDF Upload
    │
    ▼
PyMuPDF Text Extraction
    │
    ├── Text Found ──────► Continue Processing
    │
    └── No Text Found
            │
            ▼
       PDF → Images
            │
            ▼
        Tesseract OCR
            │
            ▼
       Extracted Text
```

This allows the platform to process:

* Standard text-based PDFs
* Scanned PDFs
* Image-based documents
* Documents containing screenshots or scanned pages

---

### ⚡ Asynchronous Processing

Heavy processing tasks are executed asynchronously using FastAPI background processing.

Tasks include:

* Document parsing
* OCR processing
* Text chunking
* Embedding generation
* Vector database insertion

This keeps the API responsive while large documents are being processed.

---

### 🔎 Contextual Querying

User queries are converted into embeddings and matched against the knowledge base using vector similarity search.

The most relevant chunks are then provided to `gpt-4o` as context to generate an answer.

```text
User Query
     │
     ▼
Query Embedding
     │
     ▼
ChromaDB Similarity Search
     │
     ▼
Top-K Relevant Chunks
     │
     ▼
GPT-4o + Retrieved Context
     │
     ▼
Generated Answer
```

The API also returns the retrieved context and similarity scores for better transparency and debugging.

---

### 📊 Structured Logging & Telemetry

The application provides structured logging throughout the document and query lifecycle.

Tracked metrics include:

* Document ingestion status
* Text extraction time
* OCR fallback activation
* Number of generated chunks
* Embedding generation latency
* Vector database write operations
* Vector search distances
* OpenAI API latency
* Query processing time

Example:

```text
INFO  Document upload received
INFO  Extracted 12,450 characters from PDF
INFO  OCR fallback activated
INFO  Generated 42 chunks
INFO  Generated embeddings for 42 chunks
INFO  Stored 42 vectors in ChromaDB
INFO  Query completed in 1.82s
```

---

# 🏗️ Architecture

```text
                         ┌──────────────────┐
                         │      Client      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     FastAPI      │
                         │      Backend     │
                         └────────┬─────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
                  ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │   Documents   │               │     Query     │
          │    Upload     │               │    Endpoint   │
          └───────┬───────┘               └───────┬───────┘
                  │                               │
                  ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │ Text / PDF    │               │ Query         │
          │ Extraction    │               │ Embedding     │
          └───────┬───────┘               └───────┬───────┘
                  │                               │
                  ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │ OCR Fallback  │               │   ChromaDB    │
          │  (Tesseract)  │               │ Vector Search │
          └───────┬───────┘               └───────┬───────┘
                  │                               │
                  ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │   Chunking    │               │ Relevant      │
          │               │               │ Context       │
          └───────┬───────┘               └───────┬───────┘
                  │                               │
                  ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │   OpenAI      │               │    GPT-4o      │
          │  Embeddings   │               │ Answer        │
          └───────┬───────┘               └───────┬───────┘
                  │                               │
                  ▼                               ▼
          ┌────────────────────────────────────────────┐
          │                  ChromaDB                   │
          │            Persistent Vector Store          │
          └────────────────────────────────────────────┘
```

---

# 🛠️ Tech Stack

| Component            | Technology                      |
| -------------------- | ------------------------------- |
| Backend Framework    | FastAPI                         |
| Programming Language | Python 3.9+                     |
| Vector Database      | ChromaDB                        |
| LLM                  | OpenAI GPT-4o                   |
| Embedding Model      | OpenAI `text-embedding-3-small` |
| PDF Processing       | PyMuPDF                         |
| OCR                  | Tesseract                       |
| PDF → Image          | pdf2image                       |
| API Server           | Uvicorn                         |
| Validation           | Pydantic                        |
| File Uploads         | python-multipart                |

---

# 📋 Supported Documents

The platform supports:

* `.pdf`
* `.txt`
* `.md`
* `.py`
* `.js`
* `.ts`
* `.java`
* `.cpp`
* `.c`
* `.json`
* Other supported text/code files

---

# ⚙️ Prerequisites

## 1. System Dependencies

OCR functionality requires **Tesseract** and **Poppler**.

### Ubuntu / Debian

```bash
sudo apt-get update

sudo apt-get install -y \
    tesseract-ocr \
    poppler-utils
```

### macOS

Using Homebrew:

```bash
brew install tesseract
brew install poppler
```

### Windows

Install:

* Tesseract OCR
* Poppler

Make sure their installation directories are available in your system `PATH`.

---

# 🐍 Python Environment

Python **3.9 or higher** is required.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```powershell
venv\Scripts\activate
```

---

# 📦 Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/ai-knowledge-platform.git
```

Navigate into the project:

```bash
cd ai-knowledge-platform
```

Install dependencies:

```bash
pip install fastapi \
    uvicorn \
    chromadb \
    openai \
    pydantic \
    python-multipart \
    pymupdf \
    pytesseract \
    pdf2image
```

Alternatively, if a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Alternatively, export the API key directly:

### Linux / macOS

```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key-here"
```

> **Security:** Never commit your `.env` file or OpenAI API key to GitHub.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
chroma/
```

---

# ▶️ Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:

```text
http://localhost:8000
```

---

# 📚 API Documentation

FastAPI automatically provides interactive Swagger documentation.

Open:

```text
http://localhost:8000/docs
```

Alternative ReDoc documentation:

```text
http://localhost:8000/redoc
```

---

# 🔌 API Reference

## 1. Upload a Document

Uploads a document and queues it for asynchronous processing.

### Endpoint

```http
POST /documents
```

### Content-Type

```text
multipart/form-data
```

### Supported Files

```text
.pdf
.txt
.md
.py
.js
.ts
.java
.cpp
.c
...
```

### Example Response

```json
{
  "document_id": "b4f13a01-92e1-4a...",
  "filename": "Knowledge_Base_Sample.pdf",
  "status": "PROCESSING_QUEUED"
}
```

### Processing Flow

```text
Upload
  ↓
Document Validation
  ↓
Text Extraction
  ↓
OCR Fallback (if required)
  ↓
Chunk Generation
  ↓
Embedding Generation
  ↓
ChromaDB Storage
```

---

# 2. Query the Knowledge Base

Performs semantic vector search and generates an answer using the retrieved context.

### Endpoint

```http
POST /query
```

### Content-Type

```text
application/json
```

### Request

```json
{
  "query": "What are the core capabilities of the AI orchestration platform?",
  "top_k": 5
}
```

### Response

```json
{
  "answer": "The platform automates complex workflows, connects every app securely, and controls AI at scale with IT-grade governance.",
  "context_used": [
    {
      "chunk_id": "b4f13a01-92e1-4a..._chunk_4",
      "document_id": "b4f13a01-92e1-4a...",
      "content": "Automate complex workflows with ease...",
      "similarity_score": 0.21
    }
  ]
}
```

### Query Flow

```text
Question
   ↓
Embedding Generation
   ↓
ChromaDB Similarity Search
   ↓
Top-K Context
   ↓
GPT-4o
   ↓
Answer + Context
```

---

# 3. Delete a Document

Permanently removes a document and its associated vectors from ChromaDB.

### Endpoint

```http
DELETE /documents/{document_id}
```

### Example

```http
DELETE /documents/b4f13a01-92e1-4a...
```

### Response

```json
{
  "status": "SUCCESS",
  "message": "Document b4f13a01... and its vectors have been deleted."
}
```

---

# 🗄️ Vector Database

The platform uses **ChromaDB** as a persistent local vector database.

Document chunks are stored with metadata such as:

```json
{
  "document_id": "b4f13a01...",
  "chunk_id": "b4f13a01..._chunk_4",
  "filename": "Knowledge_Base_Sample.pdf"
}
```

The vector database enables semantic retrieval based on embedding similarity rather than simple keyword matching.

---

# 🧩 RAG Pipeline

The complete RAG pipeline consists of two major stages.

## Ingestion

```text
Document
   ↓
Text Extraction
   ↓
OCR (if required)
   ↓
Text Cleaning
   ↓
Semantic Chunking
   ↓
OpenAI Embeddings
   ↓
ChromaDB
```

## Retrieval & Generation

```text
User Query
   ↓
Query Embedding
   ↓
Vector Similarity Search
   ↓
Top-K Chunks
   ↓
Context Construction
   ↓
GPT-4o
   ↓
Final Answer
```

---

# 🔍 Similarity Search

The system uses vector similarity to identify the most relevant document chunks.

Each retrieved chunk contains a similarity score:

```json
{
  "chunk_id": "document_chunk_4",
  "similarity_score": 0.21
}
```

This makes it possible to inspect which pieces of knowledge were used to generate the response.

---

# 📈 Logging & Monitoring

The application uses Python's structured logging capabilities to monitor system activity.

Example lifecycle:

```text
INFO  Upload started: Knowledge_Base_Sample.pdf
INFO  PDF text extraction completed
INFO  Extracted characters: 12,450
INFO  Generated chunks: 42
INFO  Generating embeddings
INFO  Embeddings generated successfully
INFO  Stored vectors in ChromaDB
INFO  Query received
INFO  Retrieved top 5 chunks
INFO  OpenAI response generated
INFO  Query latency: 1.82s
```

Key metrics include:

| Metric             | Description                            |
| ------------------ | -------------------------------------- |
| Extraction Time    | Time required to extract document text |
| OCR Activation     | Whether OCR fallback was required      |
| Chunk Count        | Number of generated chunks             |
| Embedding Latency  | Time required to generate embeddings   |
| Vector Write Time  | Time required to store vectors         |
| Search Latency     | Time required for vector search        |
| LLM Latency        | Time required to generate the answer   |
| End-to-End Latency | Total query processing time            |

---

# 📁 Suggested Project Structure

```text
ai-knowledge-platform/
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── data/
│   └── uploads/
│
├── chroma/
│   └── ...
│
├── logs/
│   └── application.log
│
└── tests/
    ├── test_documents.py
    └── test_query.py
```

---

# 🧪 Testing

Run the application:

```bash
uvicorn main:app --reload
```

Then open Swagger:

```text
http://localhost:8000/docs
```

From Swagger UI you can test:

```text
POST   /documents
POST   /query
DELETE /documents/{document_id}
```

---

# 🔒 Security Considerations

For production deployments, consider implementing:

* API authentication and authorization
* Request rate limiting
* File size restrictions
* Allowed file-type validation
* Malware scanning for uploaded files
* Input validation
* Prompt-injection protection
* Sensitive-data detection/redaction
* Secure API-key management
* HTTPS/TLS
* Access control for documents
* Audit logging
* Vector database access controls

**Never expose your OpenAI API key in source code or commit it to Git.**

---

# 🚀 Production Considerations

For a production deployment, the following improvements are recommended:

### Background Processing

Replace FastAPI in-process background tasks with a dedicated job queue such as:

* Celery
* Redis Queue
* RabbitMQ
* AWS SQS

This provides better reliability for long-running OCR and embedding jobs.

### Vector Database

For larger enterprise deployments, consider:

* ChromaDB
* PostgreSQL + pgvector
* Qdrant
* Weaviate
* Pinecone

### Observability

Consider integrating:

* Prometheus
* Grafana
* OpenTelemetry
* ELK / OpenSearch
* CloudWatch

### Deployment

The application can be containerized using Docker:

```text
                    ┌──────────────────┐
                    │     Client       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Load Balancer  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │    Containers    │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ Job Workers  │          │ Vector Store │
        │ OCR/Embedding│          │  ChromaDB    │
        └──────────────┘          └──────────────┘
```

---

# 🧠 Example Use Cases

The platform can be used for enterprise knowledge applications such as:

* Internal company knowledge assistants
* HR knowledge bases
* Technical documentation search
* Policy and compliance assistants
* Engineering documentation
* Codebase knowledge retrieval
* Product documentation assistants
* Enterprise PDF search
* Research document retrieval
* Customer support knowledge bases

---

# 🛣️ Future Enhancements

Potential improvements include:

* [ ] Document versioning
* [ ] User authentication
* [ ] Role-based document access
* [ ] Multi-tenant knowledge bases
* [ ] Hybrid keyword + vector search
* [ ] Re-ranking models
* [ ] Streaming LLM responses
* [ ] Document status tracking API
* [ ] Batch document ingestion
* [ ] Metadata filtering
* [ ] Conversation history
* [ ] Citation generation
* [ ] Page-level PDF citations
* [ ] Image and table extraction
* [ ] Advanced OCR
* [ ] Redis/Celery-based task queues
* [ ] PostgreSQL + pgvector support
* [ ] Docker deployment
* [ ] Prometheus/Grafana monitoring
* [ ] Automated evaluation of RAG responses

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

3. Make your changes
4. Run tests
5. Commit your changes

```bash
git commit -m "Add my feature"
```

6. Push the branch

```bash
git push origin feature/my-feature
```

7. Open a Pull Request

---

# 📄 License

Add your project license here.

Example:

```text
MIT License
```

---

# ⭐ Project Summary

**Enterprise AI Knowledge Platform** provides a complete backend foundation for building enterprise RAG applications.

It combines:

* ⚡ FastAPI
* 🧠 OpenAI GPT-4o
* 🔢 OpenAI text embeddings
* 🗄️ ChromaDB
* 📄 PyMuPDF
* 👁️ Tesseract OCR
* 🔄 Asynchronous processing
* 📊 Structured logging
* 🔎 Semantic retrieval

into a single extensible backend platform for enterprise knowledge retrieval and AI-powered question answering.
