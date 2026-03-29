# BC Admissions Email Assistant — Backend

FastAPI backend that generates email responses using Brooklyn College admissions templates.

## Setup

```bash
# 1. Navigate to backend folder
cd backend

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your HF token
cp .env.example .env
# Edit .env and paste your Hugging Face token

# 5. Add your template DOCX
# Place your admissions template DOCX file in the templates/ folder

# 6. Run the server
uvicorn main:app --reload
```

The API will be running at `http://localhost:8000`

## API Endpoints

### `GET /api/health`
Health check — shows loaded templates count.

### `GET /api/templates`
Lists all available template titles.

### `POST /api/generate`
Generate a response for a student email.

**Request:**
```json
{
  "email_text": "Hi, my name is Sarah Chen. I applied for Fall 2026 and my CUNYfirst says under review."
}
```

**Response:**
```json
{
  "success": true,
  "student_name": "Sarah Chen",
  "student_semester": "Fall 2026",
  "student_topic": "application status under review",
  "template_title": "STATUS OF APPLICATION WHEN CUNYFIRST CHECKLIST...",
  "response_text": "Dear Sarah Chen, ...",
  "docx_download_url": "/api/download/response_abc12345.docx",
  "confidence": 39.59,
  "message": "Response generated successfully."
}
```

### `GET /api/download/{filename}`
Download a generated DOCX response file.

## API Docs
Visit `http://localhost:8000/docs` for interactive Swagger documentation.
