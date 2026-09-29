import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
import chromadb
import fitz
import io
import time
from dotenv import load_dotenv
import logging
from pdf2image import convert_from_bytes
import pytesseract

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION & CLIENTS ---
# Set your OPENAI_API_KEY in the environment variables
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Outputs to stdout / terminal
    ]
)
logger = logging.getLogger("rag_pipeline")

# ==========================================
# CONFIGURATION & CLIENTS
# ==========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.critical("OPENAI_API_KEY environment variable is missing!")
    raise ValueError("OPENAI_API_KEY environment variable is missing.")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger.info("Initializing ChromaDB persistent client at './chroma_data'...")
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(
    name="internal_knowledge",
    metadata={"hnsw:space": "cosine"}
)
logger.info("ChromaDB collection 'internal_knowledge' ready.")

app = FastAPI(title="End-to-End RAG Platform with Structured Logging")

# ==========================================
# SCHEMAS
# ==========================================
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    document_ids: Optional[List[str]] = None

class ContextChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float

class QueryResponse(BaseModel):
    answer: str
    context_used: List[ContextChunk]

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str

# ==========================================
# HELPER FUNCTIONS WITH LOGGING
# ==========================================
def extract_text(file_content: bytes, filename: str) -> str:
    """Extracts text using PyMuPDF, falling back to OCR for scanned/image-based PDFs."""
    start_time = time.time()
    extracted = ""
    file_size_kb = len(file_content) / 1024
    logger.info(f"Starting text extraction for file '{filename}' ({file_size_kb:.2f} KB)...")

    if filename.lower().endswith(".pdf"):
        try:
            # Attempt standard fast text extraction
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            total_pages = len(pdf_document)
            logger.info(f"Parsing PDF document with {total_pages} pages using PyMuPDF...")
            
            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text("text")
                extracted += page_text + "\n"
            
            pdf_document.close()

            # --- OCR FALLBACK LOGIC ---
            if not extracted.strip():
                logger.warning(f"No text layer found in '{filename}'. Activating OCR fallback...")
                extracted = "" # Reset just in case
                
                # Convert PDF bytes to a list of PIL Images
                images = convert_from_bytes(file_content)
                logger.info(f"Converted {len(images)} pages to images. Running Tesseract OCR...")
                
                for i, img in enumerate(images):
                    text = pytesseract.image_to_string(img)
                    extracted += text + "\n"
                    logger.info(f"OCR completed for page {i+1}/{len(images)}.")

        except Exception as e:
            logger.error(f"Failed to read PDF '{filename}': {str(e)}")
    else:
        logger.info(f"Parsing plain text / code file '{filename}'...")
        extracted = file_content.decode("utf-8", errors="ignore")

    cleaned_text = extracted.strip()
    elapsed = time.time() - start_time
    logger.info(f"Extraction completed in {elapsed:.3f}s. Extracted {len(cleaned_text)} characters.")
    return cleaned_text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Splits text into overlapping chunks, filtering out whitespace-only chunks."""
    start_time = time.time()
    if not text:
        logger.warning("Chunking skipped: Source text is empty.")
        return []

    raw_chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            raw_chunks.append(chunk)
        start += (chunk_size - overlap)

    elapsed = time.time() - start_time
    logger.info(f"Chunking completed in {elapsed:.3f}s. Generated {len(raw_chunks)} chunks (size: {chunk_size}, overlap: {overlap}).")
    return raw_chunks


async def process_document_pipeline(document_id: str, filename: str, content: bytes):
    """Background task to extract, chunk, embed, and store document data."""
    logger.info(f"[TASK START] Processing document ID: {document_id} ('{filename}')")
    task_start = time.time()

    try:
        # 1. Extraction
        text = extract_text(content, filename)
        if not text:
            logger.error(f"[TASK FAILED] Document ID {document_id}: No usable text extracted.")
            return

        # 2. Chunking
        chunks = chunk_text(text)
        if not chunks:
            logger.error(f"[TASK FAILED] Document ID {document_id}: No valid chunks generated.")
            return

        # 3. Embeddings Generation
        logger.info(f"Requesting embeddings from OpenAI model 'text-embedding-3-small' for {len(chunks)} chunks...")
        embed_start = time.time()
        response = await openai_client.embeddings.create(
            input=chunks,
            model="text-embedding-3-small"
        )
        embeddings = [data.embedding for data in response.data]
        logger.info(f"Embeddings generated successfully in {time.time() - embed_start:.3f}s.")

        # 4. Storage in ChromaDB
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": document_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))]

        logger.info(f"Writing {len(chunks)} vectors to ChromaDB collection...")
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        total_elapsed = time.time() - task_start
        logger.info(f"[TASK SUCCESS] Document ID {document_id} fully indexed in {total_elapsed:.3f}s.")

    except Exception as e:
        logger.exception(f"[TASK ERROR] Unexpected error while processing document ID {document_id}: {str(e)}")

# ==========================================
# API ENDPOINTS WITH LOGGING
# ==========================================

@app.post("/documents", response_model=DocumentResponse)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Ingests a document, extracts text, and queues it for the embedding pipeline."""
    document_id = str(uuid.uuid4())
    logger.info(f"POST /documents - Received upload request for file '{file.filename}'. Assigned ID: {document_id}")
    
    content = await file.read()
    
    # Queue background task
    background_tasks.add_task(process_document_pipeline, document_id, file.filename, content)
    logger.info(f"Queued background processing task for document ID {document_id}.")

    return DocumentResponse(
        document_id=document_id,
        filename=file.filename,
        status="PROCESSING_QUEUED"
    )

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Retrieves relevant document chunks and generates an AI answer based on the context."""
    query_start = time.time()
    logger.info(f"POST /query - Processing query: '{request.query}' (top_k={request.top_k}, doc_filter={request.document_ids})")

    # 1. Embed the user query
    logger.info("Generating query vector via OpenAI embeddings API...")
    embed_start = time.time()
    query_embed_response = await openai_client.embeddings.create(
        input=request.query,
        model="text-embedding-3-small"
    )
    query_vector = query_embed_response.data[0].embedding
    logger.info(f"Query embedding generated in {time.time() - embed_start:.3f}s.")

    # 2. Filter metadata (if requested)
    where_filter = None
    if request.document_ids:
        if len(request.document_ids) == 1:
            where_filter = {"document_id": request.document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": request.document_ids}}
        logger.info(f"Applying metadata filter: {where_filter}")

    # 3. Vector Similarity Search
    logger.info("Executing vector similarity search in ChromaDB...")
    db_search_start = time.time()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=request.top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    logger.info(f"Vector search returned results in {time.time() - db_search_start:.3f}s.")

    if not results["ids"] or not results["ids"][0]:
        logger.warning(f"No relevant vector matches found for query: '{request.query}'")
        return QueryResponse(
            answer="I couldn't find any relevant information in the knowledge base.",
            context_used=[]
        )

    # 4. Construct Context for LLM
    context_chunks = []
    combined_context = ""
    retrieved_count = len(results["ids"][0])
    logger.info(f"Retrieved {retrieved_count} candidate chunks from ChromaDB:")

    for i in range(retrieved_count):
        chunk_id = results["ids"][0][i]
        chunk_text_val = results["documents"][0][i]
        doc_id = results["metadatas"][0][i]["document_id"]
        score = results["distances"][0][i]

        logger.info(f"  [{i+1}/{retrieved_count}] Chunk ID: {chunk_id} | Doc ID: {doc_id} | Distance Score: {score:.4f}")

        context_chunks.append(ContextChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            content=chunk_text_val,
            similarity_score=score
        ))
        combined_context += f"\n\n--- Document ID: {doc_id} ---\n{chunk_text_val}"

    # 5. RAG Generation: Ask LLM using the retrieved context
    system_prompt = (
        "You are an internal developer assistant. Answer the user's question purely based on the provided context below. "
        "If the answer is not contained in the context, state that clearly. Do not make up information."
    )
    user_prompt = f"Context:\n{combined_context}\n\nQuestion: {request.query}"

    logger.info("Sending context and query to OpenAI gpt-4o for completion...")
    llm_start = time.time()
    llm_response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    llm_elapsed = time.time() - llm_start
    total_query_latency = time.time() - query_start
    logger.info(f"LLM completed response in {llm_elapsed:.3f}s. Total /query pipeline latency: {total_query_latency:.3f}s.")

    return QueryResponse(
        answer=llm_response.choices[0].message.content,
        context_used=context_chunks
    )

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Hard deletes all vector chunks associated with a document ID."""
    logger.info(f"DELETE /documents/{document_id} - Initiating document deletion...")
    try:
        collection.delete(where={"document_id": document_id})
        logger.info(f"Successfully purged all vectors associated with document ID: {document_id}")
        return {"status": "SUCCESS", "message": f"Document {document_id} and its vectors have been deleted."}
    except Exception as e:
        logger.error(f"Failed to delete document ID {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)