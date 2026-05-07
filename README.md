# BC Admissions Email Assistant

An AI-powered email response tool built for the Brooklyn College Office of Undergraduate Admissions. Staff paste a student inquiry, and the system automatically identifies the correct response template, fills in the student's name and semester, and returns a formatted response ready to copy into an email client.

**Live App:** [cisc-4900-final-project.vercel.app](https://cisc-4900-final-project.vercel.app)

---

## Problem

The Brooklyn College admissions office handles over 50 student emails per day. Many of these are repetitive questions about application status, transfer requirements, fee waivers, and campus tours. Staff manually search through a Word document containing 27 response templates, copy the relevant section, and edit it for each student. This process is time-consuming and error-prone during peak periods.

## Solution

This application automates that workflow. Staff paste the student's email, and the system:

1. Extracts the student's name, semester, and topic using an LLM
2. Retrieves the best matching template using BM25 keyword search
3. Verifies the match using an LLM as a second check
4. Fills in the student's name and semester while preserving all original formatting
5. Displays the formatted response with bold text, bullet points, and hyperlinks
6. Provides one-click copy (with formatting) and Word document download

The system does not generate new content. It only retrieves and personalizes approved templates from the admissions office's own document.

---

## Screenshots

### Email Response Generator
Paste a student email on the left. The system identifies the correct template and returns a personalized, formatted response on the right.

![Email Response Generator](screenshots/response.png)

### Home Page
Clean two-panel layout with sidebar navigation.

![Home Page](screenshots/home.png)

### Template Browser
Browse all 27 response templates with search and expandable previews.

![Templates](screenshots/templates.png)

### Analytics Dashboard
Track total queries, match rates, most used templates, and staff feedback.

![Dashboard](screenshots/dashboard.png)

### Sensitive Information Detection
The system blocks processing if it detects SSNs, phone numbers, addresses, dates of birth, or credit card numbers. The data never reaches the AI.

![Sensitive Info Warning](screenshots/sensitive.png)

---

## Features

- **Template matching** using BM25 retrieval with title boosting, verified by Llama 3.1 8B
- **Student info extraction** — automatically detects name and semester from the email
- **Placeholder filling** — replaces "Dear Applicant" and "[specific semester]" at the run level, preserving all Word document formatting (bold, italic, underline)
- **Formatted HTML response** — displays bold text, bullet points, and hyperlinks exactly as they appear in the original Word document
- **Copy with formatting** — one-click copy that preserves rich text when pasted into Gmail, Outlook, or other email clients
- **Word document download** — exports the response as a .docx file with original formatting intact
- **Sensitive information detection** — blocks SSN, phone numbers, home addresses, dates of birth, and credit card numbers before they reach the AI
- **Confidence threshold** — returns "No matching template found" when the system is not confident, rather than sending a wrong response
- **Template browser** — searchable list of all 27 templates with expandable previews
- **Analytics dashboard** — tracks total queries, match/unmatch rates, most used templates, average confidence scores, and staff feedback
- **Feedback system** — Yes/No feedback buttons on each response, stored in MongoDB for tracking response quality
- **Edge case handling** — handles missing names, first-name-only signatures, typos, vague emails, and irrelevant questions

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18, Vite 5 | User interface |
| Backend | FastAPI, Python 3.12 | API server |
| Retrieval | BM25 (rank-bm25) | Template matching |
| LLM | Llama 3.1 8B Instruct | Info extraction and template verification |
| LLM API | Hugging Face Inference API | Hosted model access |
| Document Processing | python-docx | Read/write Word documents |
| Database | MongoDB Atlas | Query logging and analytics |
| Frontend Hosting | Vercel | Free tier, auto-deploy |
| Backend Hosting | Render | Free tier, Docker container |
| Dev Environment | GitHub Codespaces | Cloud IDE with auto-configured ports |

---

## Architecture

```
Student Email
     │
     ▼
┌─────────────────────────────────────┐
│  Frontend (React + Vite on Vercel)  │
│  - Sensitive info check (browser)   │
│  - Paste email → Generate Response  │
│  - Copy with formatting / Download  │
└──────────────┬──────────────────────┘
               │ POST /api/generate
               ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI on Render)        │
│                                     │
│  1. Extract name, semester, topic   │
│     └── LLM call (Llama 3.1 8B)    │
│                                     │
│  2. BM25 retrieval (top 5)         │
│     └── Title boosted 3x           │
│                                     │
│  3. LLM picks best template        │
│     └── Confidence threshold: 8.0   │
│                                     │
│  4. Fill placeholders (run-level)   │
│     └── Preserves bold/formatting   │
│                                     │
│  5. Generate HTML + DOCX output     │
│                                     │
│  6. Log to MongoDB (anonymized)     │
└─────────────────────────────────────┘
```

---

## Project Structure

```
CISC-4900-Final-Project/
├── .devcontainer/
│   └── devcontainer.json          # Auto-configure Codespaces ports
├── backend/
│   ├── main.py                    # All backend logic (FastAPI + BM25 + LLM + MongoDB)
│   ├── requirements.txt           # Python dependencies
│   ├── templates/
│   │   └── admissions_templates.docx
│   └── outputs/                   # Generated DOCX files (auto-cleaned)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main React component (all pages)
│   │   ├── index.css              # Brooklyn College branded styles
│   │   ├── main.jsx               # React entry point
│   │   └── api/
│   │       └── client.js          # API client
│   ├── index.html                 # HTML entry with Google Fonts
│   ├── package.json
│   └── vite.config.js
├── archive/                       # Original Colab notebooks
├── screenshots/                   # App screenshots for README
├── Dockerfile                     # Docker config for Render
├── setup.sh                       # One-command dev setup
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server status, template count, MongoDB connection |
| GET | `/api/templates` | List of all 27 templates with text content |
| POST | `/api/generate` | Main pipeline — takes email, returns formatted response |
| POST | `/api/feedback` | Save Yes/No feedback for a query |
| GET | `/api/dashboard` | Analytics data (totals, top templates, recent queries) |
| GET | `/api/download/{filename}` | Download generated DOCX file |

---

## Running Locally

### Prerequisites
- Python 3.12+
- Node.js 18+
- Hugging Face account with API token
- MongoDB Atlas account (free tier)

### Quick Start (GitHub Codespaces)

1. Open the repo in GitHub Codespaces
2. Run the setup script:
   ```bash
   bash setup.sh
   ```
3. Create the backend environment file:
   ```bash
   echo "HF_TOKEN=your_huggingface_token
   MONGO_URI=your_mongodb_connection_string" > backend/.env
   ```
4. Start the backend:
   ```bash
   cd backend && source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --reload
   ```
5. Start the frontend (new terminal):
   ```bash
   cd frontend && npm run dev
   ```
6. Set both ports (3000 and 8000) to Public in the Ports tab

---

## Testing

The system was tested with 10 standard email scenarios and 5 edge cases. All 15 passed correctly.

**Standard tests:** application status, accept offer, decline offer, campus tour, transfer requirements, fee waiver, financial aid, film studies program, TOEFL scores, commitment deposit.

**Edge cases:** no name in email, first-name-only signature, vague one-word email, email with typos, irrelevant question (returns "no match").

---

## Deployment

- **Frontend** is deployed on [Vercel](https://vercel.com) (free tier, never sleeps)
- **Backend** is deployed on [Render](https://render.com) (free tier, sleeps after 15 min of inactivity)
- **Database** is on [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier, 512MB)
- All three auto-deploy when code is pushed to the main branch

---

## Author

**Saifuzzaman Tanim**
CISC 4900 — Senior Project
Brooklyn College, Spring 2026
