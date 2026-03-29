"""
main.py — FastAPI backend for BC Admissions Email Response Generator.

API Endpoints:
  POST /api/generate    → Generate a response for a student email
  GET  /api/templates   → List all available templates
  GET  /api/health      → Health check
"""

import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from retrieval import TemplateRetriever
from generator import LLMGenerator

# ── Load environment ──
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN is missing. Add it to your .env file.")

# ── Initialize components ──
TEMPLATE_DIR = Path(__file__).parent / "templates"
DOCX_FILES = list(TEMPLATE_DIR.glob("*.docx"))

if not DOCX_FILES:
    raise FileNotFoundError(
        f"No DOCX files found in {TEMPLATE_DIR}. "
        "Place your template DOCX file in the backend/templates/ folder."
    )

DOCX_PATH = str(DOCX_FILES[0])
print(f"Loading template: {DOCX_PATH}")

retriever = TemplateRetriever(DOCX_PATH)
generator = LLMGenerator(HF_TOKEN)

print(f"Loaded {len(retriever.sections)} templates")

# ── Output directory for generated DOCX files ──
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── FastAPI app ──
app = FastAPI(
    title="BC Admissions Email Assistant",
    description="AI-powered email response generator for Brooklyn College admissions",
    version="2.0",
)

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ──

class EmailRequest(BaseModel):
    email_text: str

class GenerateResponse(BaseModel):
    success: bool
    student_name: str
    student_semester: str
    student_topic: str
    template_title: str
    response_text: str
    docx_download_url: str
    confidence: float
    message: str

class NoMatchResponse(BaseModel):
    success: bool
    student_name: str
    student_topic: str
    message: str

class TemplateListResponse(BaseModel):
    templates: list[str]
    count: int


# ── API Routes ──

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "templates_loaded": len(retriever.sections),
        "docx_file": Path(DOCX_PATH).name,
    }


@app.get("/api/templates", response_model=TemplateListResponse)
def list_templates():
    """List all available email templates."""
    titles = retriever.get_template_list()
    return TemplateListResponse(templates=titles, count=len(titles))


@app.post("/api/generate")
def generate_response(request: EmailRequest):
    """
    Generate an email response for a student email.

    Pipeline:
    1. Extract student info (name, semester, topic)
    2. Retrieve top-5 templates via BM25
    3. LLM picks the best template
    4. Fill placeholders (name, semester)
    5. Export formatted DOCX
    6. Return response text + download link
    """
    email_text = request.email_text.strip()

    if not email_text:
        raise HTTPException(status_code=400, detail="Email text cannot be empty.")

    if len(email_text) < 3:
        raise HTTPException(status_code=400, detail="Email text is too short.")

    # Step 1: Extract student info
    student_info = generator.extract_student_info(email_text)

    # Step 2: Retrieve candidates
    candidates = retriever.retrieve(email_text, k=5)

    # Step 3: LLM picks template
    chosen_idx = generator.choose_template(email_text, candidates)

    # No match found
    if chosen_idx == -1:
        return {
            "success": False,
            "student_name": student_info["name"] or "(not found)",
            "student_topic": student_info["topic"],
            "message": "No matching template found. This email may need a manual response.",
        }

    chosen = candidates[chosen_idx]

    # Step 4: Fill placeholders
    working_doc = retriever.fill_placeholders(chosen, student_info)

    # Step 5: Export DOCX
    file_id = str(uuid.uuid4())[:8]
    docx_filename = f"response_{file_id}.docx"
    docx_path = OUTPUT_DIR / docx_filename
    retriever.export_docx(working_doc, chosen, str(docx_path))

    # Step 6: Get plain text
    response_text = retriever.get_plain_text(working_doc, chosen)

    return {
        "success": True,
        "student_name": student_info["name"] or "(not found)",
        "student_semester": student_info["semester"] or "(not specified)",
        "student_topic": student_info["topic"],
        "template_title": chosen["title"],
        "response_text": response_text,
        "docx_download_url": f"/api/download/{docx_filename}",
        "confidence": round(chosen["score"], 2),
        "message": "Response generated successfully.",
    }


@app.get("/api/download/{filename}")
def download_docx(filename: str):
    """Download a generated DOCX response file."""
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ── Run with: uvicorn main:app --reload ──
