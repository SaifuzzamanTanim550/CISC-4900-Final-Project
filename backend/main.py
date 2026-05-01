"""
BC Admissions Email Assistant — Backend
All logic in one file matching the Colab notebook.
Run with: uvicorn main:app --host 0.0.0.0 --reload
"""

import os
import re
import copy
import json
import uuid
import requests as http_requests
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from docx import Document
from docx.oxml.ns import qn
from rank_bm25 import BM25Okapi

# ── Load .env ──
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN", "")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set in .env")

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
CONFIDENCE_THRESHOLD = 8.0

# ── Load DOCX template ──
TEMPLATE_DIR = Path(__file__).parent / "templates"
DOCX_FILES = list(TEMPLATE_DIR.glob("*.docx"))
if not DOCX_FILES:
    raise FileNotFoundError(f"No .docx in {TEMPLATE_DIR}. Put your template there.")

DOCX_PATH = str(DOCX_FILES[0])
ORIGINAL_DOC = Document(DOCX_PATH)
print(f"Loaded: {DOCX_PATH} ({len(ORIGINAL_DOC.paragraphs)} paragraphs)")

# ── Output dir ──
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# LLM HELPER
# ═══════════════════════════════════════════════════════════════

def llm_call(system_prompt, user_prompt, max_tokens=300, temperature=0):
    r = http_requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(r.text)
    return r.json()["choices"][0]["message"]["content"].strip()


# ═══════════════════════════════════════════════════════════════
# HEADING PARSER
# ═══════════════════════════════════════════════════════════════

def is_template_heading(paragraph):
    text = (paragraph.text or "").strip()
    if not text or len(text) < 10:
        return False
    runs = paragraph.runs
    if not runs:
        return False
    if text != text.upper():
        return False
    has_bold = any(r.bold is True for r in runs)
    all_none = all(r.bold is None for r in runs)
    has_false = any(r.bold is False for r in runs)
    return (has_bold or all_none) and not has_false


def build_sections(doc):
    paragraphs = doc.paragraphs
    heading_indices = [i for i, p in enumerate(paragraphs) if is_template_heading(p)]
    raw_sections = []
    for idx, h_idx in enumerate(heading_indices):
        end_idx = heading_indices[idx + 1] - 1 if idx + 1 < len(heading_indices) else len(paragraphs) - 1
        raw_sections.append({
            "title": paragraphs[h_idx].text.strip(),
            "start": h_idx,
            "end": end_idx,
        })

    skip_titles = {"ADMISSIONS FREQUENTLY ASKED INQUIRY QUESTIONS TEMPLATES"}
    cleaned = []
    i = 0
    while i < len(raw_sections):
        s = raw_sections[i]
        if s["title"] in skip_titles:
            i += 1
            continue
        if s["title"] == "OFFICE USE ONLY":
            if i + 1 < len(raw_sections):
                raw_sections[i + 1]["start"] = s["start"]
            i += 1
            continue
        if i + 1 < len(raw_sections) and raw_sections[i + 1]["title"].startswith("EXEMPTIONS"):
            s["title"] = s["title"] + " " + raw_sections[i + 1]["title"]
            s["end"] = raw_sections[i + 1]["end"]
            i += 2
        else:
            i += 1
        para_indices = list(range(s["start"], s["end"] + 1))
        text_lines = []
        for j in para_indices:
            t = (paragraphs[j].text or "").strip()
            if t:
                text_lines.append(t)
        body_text = "\n".join(text_lines[1:]) if len(text_lines) > 1 else ""
        cleaned.append({
            "title": s["title"],
            "start": s["start"],
            "end": s["end"],
            "para_indices": para_indices,
            "text": body_text,
        })
    return cleaned


def tokenize(text):
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


# ── Build BM25 index (title boosted 3x) ──
SECTIONS = build_sections(ORIGINAL_DOC)
corpus = [
    tokenize(s["title"] + " " + s["title"] + " " + s["title"] + " " + s["text"])
    for s in SECTIONS
]
BM25 = BM25Okapi(corpus)
print(f"Templates: {len(SECTIONS)}")


# ═══════════════════════════════════════════════════════════════
# EXTRACT STUDENT INFO
# ═══════════════════════════════════════════════════════════════

def extract_student_info(email_text):
    system = """extract info from student email.
only return json.
fields:
name
semester
topic

do not guess name.
if no name, return empty string."""

    response = llm_call(system, email_text, max_tokens=150)
    try:
        match = re.search(r'\{[^}]+\}', response)
        info = json.loads(match.group()) if match else {}
    except Exception:
        info = {}

    name = info.get("name", "")
    fake_names = ["john doe", "jane doe", "applicant", "student", "n/a", "none", "unknown"]
    if name.lower().strip() in fake_names:
        name = ""

    return {
        "name": name,
        "semester": info.get("semester", ""),
        "topic": info.get("topic", "general inquiry"),
    }


# ═══════════════════════════════════════════════════════════════
# TEMPLATE SELECTION
# ═══════════════════════════════════════════════════════════════

def retrieve_top_k(email, k=5):
    scores = BM25.get_scores(tokenize(email))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [{**SECTIONS[i], "score": float(scores[i])} for i in ranked]


def llm_choose(email, candidates):
    num = len(candidates)
    previews = []
    for i, c in enumerate(candidates, 1):
        body_preview = "\n".join(c["text"].splitlines()[:8])
        previews.append(f"{i}. {c['title']} | score {c['score']:.1f}\n{body_preview}")

    system = f"""pick best template.
use title + score.
if none match return 0.
only return number from 0 to {num}."""

    prompt = email + "\n\n" + "\n\n".join(previews)
    response = llm_call(system, prompt, max_tokens=5)

    if "0" in response:
        return -1
    for char in response:
        if char.isdigit():
            return int(char) - 1
    return 0


def choose_template(email):
    candidates = retrieve_top_k(email, k=5)
    if candidates[0]["score"] < CONFIDENCE_THRESHOLD:
        return None
    chosen_idx = llm_choose(email, candidates)
    if chosen_idx == -1:
        return None
    return candidates[chosen_idx]


# ═══════════════════════════════════════════════════════════════
# FILL PLACEHOLDERS
# ═══════════════════════════════════════════════════════════════

def fill_placeholders(doc, section, student_info):
    name = student_info.get("name", "")
    semester = student_info.get("semester", "")

    for idx in section["para_indices"]:
        para = doc.paragraphs[idx]
        for run in para.runs:
            if not run.text:
                continue
            if semester:
                run.text = run.text.replace("[specific semester]", semester)
            else:
                run.text = run.text.replace("[specific semester]", "the upcoming semester")
            if name:
                run.text = run.text.replace("Dear Applicant", f"Dear {name}")
                run.text = run.text.replace("Dear Student", f"Dear {name}")


def export_doc(doc, section, out="response.docx"):
    new_doc = Document()
    for p in new_doc.paragraphs:
        p._element.getparent().remove(p._element)
    body = new_doc._element.body
    for idx in section["para_indices"]:
        if idx == section["start"]:
            continue
        body.append(copy.deepcopy(doc.paragraphs[idx]._p))
    new_doc.save(out)
    return out


def get_plain_text(doc, section):
    lines = []
    for idx in section["para_indices"]:
        if idx == section["start"]:
            continue
        text = doc.paragraphs[idx].text.strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# HTML CONVERTER — preserves bold, Strong style, bullets, links
# ═══════════════════════════════════════════════════════════════

def _is_run_bold(run):
    """Check if a run is bold — handles explicit bold, inherited bold, and Strong style."""
    # Check explicit bold
    if run.bold is True:
        return True
    # Check character style (e.g., "Strong" style makes text bold)
    if run.style and run.style.font and run.style.font.bold is True:
        return True
    # Check XML-level bold element
    rPr = run._element.find(qn('w:rPr'))
    if rPr is not None:
        b = rPr.find(qn('w:b'))
        if b is not None:
            val = b.get(qn('w:val'))
            return val is None or val != '0'
    return False


def _is_run_italic(run):
    """Check if a run is italic."""
    if run.italic is True:
        return True
    if run.style and run.style.font and run.style.font.italic is True:
        return True
    return False


def _is_run_underline(run):
    """Check if a run is underlined."""
    if run.underline is True:
        return True
    if run.style and run.style.font and run.style.font.underline is True:
        return True
    return False


def get_html_text(doc, section):
    """Convert section paragraphs to HTML preserving bold, italic, underline, bullets, links."""
    html_parts = []
    in_list = False

    for idx in section["para_indices"]:
        if idx == section["start"]:
            continue
        para = doc.paragraphs[idx]
        text = para.text.strip()

        # Check if bullet
        pPr = para._element.find(qn('w:pPr'))
        is_bullet = False
        if pPr is not None:
            is_bullet = pPr.find(qn('w:numPr')) is not None

        # Empty paragraph
        if not text:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        # Build HTML by walking through XML children in order
        run_html = ""
        for child in para._element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            # Regular run
            if tag == 'r':
                t = ""
                for t_elem in child.findall(qn('w:t')):
                    t += t_elem.text or ""
                if not t:
                    continue

                t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                # Find the matching python-docx run to check formatting
                # Match by text content
                is_bold = False
                is_italic = False
                is_underline = False

                for run in para.runs:
                    if run._element is child:
                        is_bold = _is_run_bold(run)
                        is_italic = _is_run_italic(run)
                        is_underline = _is_run_underline(run)
                        break

                if is_bold:
                    t = f"<strong>{t}</strong>"
                if is_italic:
                    t = f"<em>{t}</em>"
                if is_underline:
                    t = f"<u>{t}</u>"
                run_html += t

            # Hyperlink
            elif tag == 'hyperlink':
                rid = child.get(qn('r:id'))
                rel = doc.part.rels.get(rid) if rid else None
                url = ""
                if rel and hasattr(rel, 'target_ref'):
                    url = rel.target_ref

                link_text = ""
                for r in child.findall(qn('w:r')):
                    for t_elem in r.findall(qn('w:t')):
                        link_text += t_elem.text or ""

                if not link_text:
                    link_text = url

                link_text = link_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                if url and url.startswith("http"):
                    run_html += f'<a href="{url}" target="_blank" style="color: #882345; text-decoration: underline;">{link_text}</a>'
                else:
                    run_html += link_text

        # Make any remaining plain-text URLs clickable
        url_pattern = r'(?<!href=")(https?://[^\s<>"]+)'
        run_html = re.sub(url_pattern, r'<a href="\1" target="_blank" style="color: #882345;">\1</a>', run_html)

        if is_bullet:
            if not in_list:
                html_parts.append('<ul style="margin: 8px 0 8px 20px; padding: 0; list-style-type: disc;">')
                in_list = True
            html_parts.append(f'<li style="margin: 4px 0;">{run_html}</li>')
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<p style="margin: 8px 0; line-height: 1.6;">{run_html}</p>')

    if in_list:
        html_parts.append("</ul>")

    return "".join(html_parts)


# ═══════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(title="BC Admissions Email Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmailRequest(BaseModel):
    email_text: str


@app.get("/api/health")
def health():
    return {"status": "healthy", "templates": len(SECTIONS)}


@app.get("/api/templates")
def templates():
    return {"templates": [s["title"] for s in SECTIONS], "count": len(SECTIONS)}


@app.post("/api/generate")
def generate(req: EmailRequest):
    email_text = req.email_text.strip()
    if len(email_text) < 3:
        raise HTTPException(400, "Email too short")

    student_info = extract_student_info(email_text)
    chosen = choose_template(email_text)

    if chosen is None:
        return {
            "success": False,
            "student_name": student_info["name"] or "(not found)",
            "student_topic": student_info["topic"],
            "message": "No matching template found.",
        }

    working_doc = copy.deepcopy(ORIGINAL_DOC)
    working_section = {
        "title": chosen["title"],
        "start": chosen["start"],
        "end": chosen["end"],
        "para_indices": chosen["para_indices"],
    }
    fill_placeholders(working_doc, working_section, student_info)

    file_id = str(uuid.uuid4())[:8]
    docx_filename = f"response_{file_id}.docx"
    docx_path = OUTPUT_DIR / docx_filename
    export_doc(working_doc, working_section, str(docx_path))

    response_text = get_plain_text(working_doc, working_section)
    response_html = get_html_text(working_doc, working_section)

    old_files = sorted(OUTPUT_DIR.glob("response_*.docx"), key=lambda f: f.stat().st_mtime)
    for f in old_files[:-5]:
        f.unlink()

    return {
        "success": True,
        "student_name": student_info["name"] or "(not found)",
        "student_semester": student_info["semester"] or "(not specified)",
        "student_topic": student_info["topic"],
        "template_title": chosen["title"],
        "response_text": response_text,
        "response_html": response_html,
        "docx_download_url": f"/api/download/{docx_filename}",
        "confidence": round(chosen["score"], 2),
        "message": "OK",
    }


@app.get("/api/download/{filename}")
def download(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(path), filename=filename)
