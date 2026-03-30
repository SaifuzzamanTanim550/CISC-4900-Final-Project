// In Codespaces, the backend runs on a different forwarded URL
// Change this to your backend's Codespaces URL
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export async function generateResponse(emailText) {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_text: emailText }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to generate response');
  }

  return res.json();
}

export async function getTemplateList() {
  const res = await fetch(`${API_BASE}/templates`);
  if (!res.ok) throw new Error('Failed to load templates');
  return res.json();
}

export function getDownloadUrl(path) {
  return `${API_BASE}${path.startsWith('/api') ? path.replace('/api', '') : path}`;
}
```

Then create a file called `.env` inside your `frontend/` folder with your backend's Codespaces URL:
```
VITE_API_URL=https://fluffy-trout-pjr64vvw9jppf79pg-8000.app.github.dev/api