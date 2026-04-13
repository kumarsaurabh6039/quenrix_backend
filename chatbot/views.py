import json
import os
import io
import uuid
import numpy as np

import boto3
from botocore.exceptions import ClientError

from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

# Text extraction
import PyPDF2
import pytesseract
from PIL import Image

from .models import ChatbotCategory, ChatbotDocument, TextChunk

load_dotenv()

# ── Clients ──────────────────────────────────────────────────────────────────
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-south-2"),
)

S3_BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME")
S3_REGION = os.getenv("AWS_REGION", "ap-south-2")

# ── Config ────────────────────────────────────────────────────────────────────
CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 100     # character overlap between chunks
TOP_K_CHUNKS = 5        # how many chunks to retrieve per query
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _upload_to_s3(file_bytes: bytes, key: str, content_type: str) -> str:
    """Upload bytes to S3 and return public URL."""
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_text_from_image(file_bytes: bytes) -> str:
    """OCR-extract text from an image using Tesseract."""
    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image)


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _get_embedding(text: str) -> list[float]:
    """Get OpenAI embedding for a text string."""
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=text[:8000],  # safety trim
    )
    return response.data[0].embedding


def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _retrieve_top_chunks(query_embedding: list, category_id: int, top_k: int = TOP_K_CHUNKS) -> list[str]:
    """Find the most relevant chunks for a query within a category."""
    chunks = TextChunk.objects.filter(
        document__category_id=category_id,
        document__is_processed=True,
        embedding__isnull=False,
    ).select_related('document')

    scored = []
    for chunk in chunks:
        score = _cosine_similarity(query_embedding, chunk.embedding)
        scored.append((score, chunk.chunk_text))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:top_k]]


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def category_list_create(request):
    """GET /chatbot/categories/  |  POST /chatbot/categories/"""
    if request.method == "GET":
        active_only = request.GET.get("active", "false").lower() == "true"
        qs = ChatbotCategory.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)

        data = []
        for cat in qs:
            doc_count = cat.documents.filter(is_processed=True).count()
            data.append({
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
                "is_active": cat.is_active,
                "document_count": doc_count,
                "created_at": cat.created_at.isoformat(),
            })
        return JsonResponse({"categories": data})

    if request.method == "POST":
        body = json.loads(request.body)
        name = body.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "name is required"}, status=400)
        if ChatbotCategory.objects.filter(name__iexact=name).exists():
            return JsonResponse({"error": "Category already exists"}, status=400)

        cat = ChatbotCategory.objects.create(
            name=name,
            description=body.get("description", ""),
            icon=body.get("icon", "fas fa-folder"),
            is_active=body.get("is_active", True),
        )
        return JsonResponse({"id": cat.id, "name": cat.name}, status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def category_detail(request, category_id):
    """PUT /chatbot/categories/<id>/  |  DELETE /chatbot/categories/<id>/"""
    try:
        cat = ChatbotCategory.objects.get(id=category_id)
    except ChatbotCategory.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "PUT":
        body = json.loads(request.body)
        cat.name = body.get("name", cat.name)
        cat.description = body.get("description", cat.description)
        cat.icon = body.get("icon", cat.icon)
        cat.is_active = body.get("is_active", cat.is_active)
        cat.save()
        return JsonResponse({"success": True})

    if request.method == "DELETE":
        # Delete S3 objects for all documents
        for doc in cat.documents.all():
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=doc.s3_key)
            except ClientError:
                pass
        cat.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def document_upload(request):
    """
    POST /chatbot/documents/upload/
    Multipart form: file + category_id
    1. Upload raw file to S3
    2. Extract text (PDF → PyPDF2, image → Tesseract)
    3. Chunk text
    4. Generate OpenAI embeddings for each chunk
    5. Save TextChunk rows
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    file = request.FILES.get("file")
    category_id = request.POST.get("category_id")

    if not file:
        return JsonResponse({"error": "No file provided"}, status=400)
    if not category_id:
        return JsonResponse({"error": "category_id is required"}, status=400)

    try:
        category = ChatbotCategory.objects.get(id=category_id)
    except ChatbotCategory.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    file_bytes = file.read()
    original_name = file.name
    ext = original_name.rsplit(".", 1)[-1].lower()

    # Determine file type
    if ext == "pdf":
        file_type = "pdf"
        content_type = "application/pdf"
    elif ext in ("png", "jpg", "jpeg", "gif", "webp"):
        file_type = "image"
        content_type = file.content_type or "image/jpeg"
    else:
        return JsonResponse({"error": f"Unsupported file type: .{ext}"}, status=400)

    # ── 1. Upload to S3 ──────────────────────────────────────────────────────
    unique_key = f"chatbot-docs/{category.id}/{uuid.uuid4().hex}_{original_name}"
    try:
        s3_url = _upload_to_s3(file_bytes, unique_key, content_type)
    except ClientError as e:
        return JsonResponse({"error": f"S3 upload failed: {str(e)}"}, status=500)

    # Create DB record
    doc = ChatbotDocument.objects.create(
        category=category,
        file_name=original_name,
        file_type=file_type,
        s3_key=unique_key,
        s3_url=s3_url,
        is_processed=False,
    )

    # ── 2. Extract text ──────────────────────────────────────────────────────
    try:
        if file_type == "pdf":
            raw_text = _extract_text_from_pdf(file_bytes)
        else:  # image → OCR
            raw_text = _extract_text_from_image(file_bytes)
    except Exception as e:
        doc.delete()
        return JsonResponse({"error": f"Text extraction failed: {str(e)}"}, status=500)

    if not raw_text.strip():
        doc.delete()
        return JsonResponse({"error": "Could not extract any text from the file."}, status=422)

    # ── 3. Chunk ─────────────────────────────────────────────────────────────
    chunks = _chunk_text(raw_text)

    # ── 4 & 5. Embed + save ───────────────────────────────────────────────────
    chunk_objects = []
    for idx, chunk_text in enumerate(chunks):
        embedding = _get_embedding(chunk_text)
        chunk_objects.append(
            TextChunk(
                document=doc,
                chunk_text=chunk_text,
                chunk_index=idx,
                embedding=embedding,
            )
        )

    TextChunk.objects.bulk_create(chunk_objects)
    doc.is_processed = True
    doc.chunk_count = len(chunks)
    doc.save()

    return JsonResponse({
        "success": True,
        "document_id": doc.id,
        "file_name": doc.file_name,
        "chunks_created": len(chunks),
        "s3_url": s3_url,
    }, status=201)


@csrf_exempt
def document_list(request, category_id):
    """GET /chatbot/categories/<id>/documents/"""
    try:
        category = ChatbotCategory.objects.get(id=category_id)
    except ChatbotCategory.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    docs = []
    for doc in category.documents.all():
        docs.append({
            "id": doc.id,
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "s3_url": doc.s3_url,
            "is_processed": doc.is_processed,
            "chunk_count": doc.chunk_count,
            "uploaded_at": doc.uploaded_at.isoformat(),
        })
    return JsonResponse({"documents": docs})


@csrf_exempt
def document_delete(request, doc_id):
    """DELETE /chatbot/documents/<id>/"""
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        doc = ChatbotDocument.objects.get(id=doc_id)
    except ChatbotDocument.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    # Remove from S3
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=doc.s3_key)
    except ClientError:
        pass

    doc.delete()
    return JsonResponse({"success": True})


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT VIEW  (RAG)
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def chatbot_view(request):
    """
    POST /chatbot/chat/
    Body: { "message": "...", "category_id": 3, "history": [...] }

    1. Embed user message
    2. Retrieve top-K relevant chunks from the selected category
    3. Build grounded system prompt
    4. Call GPT with conversation history
    5. Return reply
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        category_id = data.get("category_id")
        history = data.get("history", [])  # [{role, content}, ...]

        if not user_message:
            return JsonResponse({"error": "Message is required."}, status=400)

        if not category_id:
            return JsonResponse({"error": "category_id is required."}, status=400)

        # Validate category
        try:
            category = ChatbotCategory.objects.get(id=category_id, is_active=True)
        except ChatbotCategory.DoesNotExist:
            return JsonResponse({"error": "Invalid or inactive category."}, status=404)

        # ── RAG retrieval ────────────────────────────────────────────────────
        query_embedding = _get_embedding(user_message)
        relevant_chunks = _retrieve_top_chunks(query_embedding, category_id)

        if relevant_chunks:
            context_text = "\n\n---\n\n".join(relevant_chunks)
            grounded = True
        else:
            # Fallback: search all categories if no docs in selected one
            context_text = "No specific documents found for this topic."
            grounded = False

        # ── System prompt ────────────────────────────────────────────────────
        system_prompt = f"""You are a knowledgeable assistant for Quenrix LMS (Learning Management System).

Topic: {category.name}
{f'Description: {category.description}' if category.description else ''}

Your job is to answer the user's question using ONLY the context below.
If the context does not contain enough information, say so politely and suggest
the user contact support. Do not hallucinate or invent details.

--- CONTEXT START ---
{context_text}
--- CONTEXT END ---

Guidelines:
- Be concise, clear, and helpful.
- Use bullet points or numbered lists when listing multiple items.
- If asked something outside the context, politely decline and redirect.
"""

        # ── Build messages with history ──────────────────────────────────────
        messages = [{"role": "system", "content": system_prompt}]

        # Include last N turns of history
        for turn in history[-6:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({"role": "user", "content": user_message})

        # ── OpenAI call ───────────────────────────────────────────────────────
        completion = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.3,
        )

        reply = completion.choices[0].message.content

        return JsonResponse({
            "reply": reply,
            "category": category.name,
            "grounded": grounded,
            "chunks_used": len(relevant_chunks),
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
