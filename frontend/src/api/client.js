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

export function getDownloadUrl(path) {
  const cleanPath = path.replace(/^\/api/, '');
  return `${API_BASE}${cleanPath}`;
}
