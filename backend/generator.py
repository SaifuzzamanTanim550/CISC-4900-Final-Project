"""
generator.py — LLM-powered student info extraction and template selection.

Uses Hugging Face Llama to:
1. Extract student name, semester, and topic from emails
2. Pick the best template from BM25 candidates
"""

import re
import json
import requests


class LLMGenerator:
    """Handles all LLM interactions."""

    def __init__(self, hf_token, model_id="meta-llama/Llama-3.1-8B-Instruct"):
        self.hf_token = hf_token
        self.model_id = model_id
        self.router_url = "https://router.huggingface.co/v1/chat/completions"
        self.confidence_threshold = 8.0

    def _call(self, system_prompt, user_prompt, max_tokens=300, temperature=0):
        """Make a single LLM API call."""
        r = requests.post(
            self.router_url,
            headers={
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_id,
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
            raise RuntimeError(f"LLM API error ({r.status_code}): {r.text}")

        return r.json()["choices"][0]["message"]["content"].strip()

    def extract_student_info(self, email_text):
        """Extract name, semester, and topic from a student email."""
        system = """You extract information from student emails sent to a college admissions office.
Reply ONLY with a JSON object. No extra text, no markdown, no backticks.

Extract these fields:
- "name": the student's name. ONLY extract a name if it is EXPLICITLY written in the email — for example in a sign-off ("Thanks, Maria"), a greeting ("My name is Maria Lopez"), or a signature. If there is NO name written anywhere in the email, you MUST return "". Do NOT invent or guess a name. Do NOT use placeholder names like "John Doe".
- "semester": the semester they are asking about (e.g. "Fall 2026", "Spring 2026"). Look for year mentions, "next semester", "upcoming fall", etc. If not mentioned at all, use exactly "".
- "topic": a short 3-8 word summary of what they are asking about.

Examples:
- "Hi my name is Maria Lopez, I applied for Fall 2026..." → {"name": "Maria Lopez", "semester": "Fall 2026", "topic": "application status"}
- "can i get a fee waiver?? thanks - carlos" → {"name": "carlos", "semester": "", "topic": "fee waiver request"}
- "What are the transfer requirements?" → {"name": "", "semester": "", "topic": "transfer admission requirements"}
- "help" → {"name": "", "semester": "", "topic": "general help request"}"""

        user = f"Student email:\n\n{email_text}"
        response = self._call(system, user, max_tokens=150)

        try:
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                info = json.loads(json_match.group())
            else:
                info = {}
        except Exception:
            info = {}

        # Reject fake/placeholder names
        name = info.get("name", "")
        fake_names = ["john doe", "jane doe", "applicant", "student", "n/a", "none", "unknown"]
        if name.lower().strip() in fake_names:
            name = ""

        return {
            "name": name,
            "semester": info.get("semester", ""),
            "topic": info.get("topic", "general inquiry"),
        }

    def choose_template(self, email_text, candidates):
        """
        Ask LLM to pick the best template from BM25 candidates.
        Returns the index (0-based) or -1 if no match.
        """
        # Check confidence first
        if candidates[0]["score"] < self.confidence_threshold:
            return -1

        num = len(candidates)
        previews = []
        for i, c in enumerate(candidates, 1):
            body_preview = "\n".join(c["text"].splitlines()[:8])
            previews.append(
                f"Option {i}:\nTitle: {c['title']}\nBM25 Score: {c['score']:.1f}\nContent:\n{body_preview}"
            )

        system = f"""You are a template-matching assistant for the Brooklyn College admissions office.
You will be given a student email and {num} template options.

RULES:
- Choose the template that BEST matches what the student is SPECIFICALLY asking about.
- Pay very close attention to the template TITLE — it describes the exact situation the template is for.
- The BM25 Score shows how well the template matched keywords. Higher scores are usually better. If the top-scoring template clearly matches the email, prefer it.
- Read the student's email carefully for SPECIFIC keywords:
  * "under review" → STATUS OF APPLICATION WHEN CUNYFIRST CHECKLIST STATES APPLICATION IS UNDER REVIEW
  * "complete" or "being reviewed" → STATUS OF APPLICATION WHEN CUNYFIRST STATES APPLICATION IS COMPLETE AND BEING REVIEWED
  * "accept" the offer → ACCEPTANCE OF ADMISSIONS OFFER
  * "decline" the offer → DECLINE OF ADMISSIONS OFFER
  * "can I get a fee waiver" or "can't afford" → CUNY APPLICATION FEE WAIVER ELIGIBILITY
  * "how to submit fee waiver" or "steps" → STEPS TO SUBMIT AN APPLICATION FEE WAIVER REQUEST
  * "transfer requirements" or "how to transfer" → BROOKLYN COLLEGE TRANSFER ADMISSION REQUIREMENTS
  * "how long to graduate" or "time to degree" → TIME TO DEGREE COMPLETION AFTER TRANSFER
- If NONE of the templates are relevant to the student's question, reply with 0.
- Reply with ONLY the option number (0-{num}). Nothing else."""

        prompt = "Student email:\n" + email_text + "\n\nTemplates:\n" + "\n\n".join(previews)
        response = self._call(system, prompt, max_tokens=5)

        for char in response:
            if char == "0":
                return -1

        valid = [str(d) for d in range(1, num + 1)]
        for char in response:
            if char in valid:
                return int(char) - 1

        return 0
