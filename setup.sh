#!/bin/bash
# ═══════════════════════════════════════════════════
# BC Admissions Email Assistant — Setup Script
# Run this ONCE in your Codespaces terminal:
#   bash setup.sh
# ═══════════════════════════════════════════════════

echo "═══════════════════════════════════════════"
echo "  Setting up BC Admissions Email Assistant"
echo "═══════════════════════════════════════════"

# Backend setup
echo ""
echo "── Backend ──"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Backend ready."

# Frontend setup
echo ""
echo "── Frontend ──"
cd ../frontend
npm install

# Create .env with Codespaces URL
if [ -n "$CODESPACE_NAME" ]; then
    echo "VITE_API_URL=https://${CODESPACE_NAME}-8000.app.github.dev/api" > .env
    echo "Created frontend/.env:"
    cat .env
else
    echo "VITE_API_URL=/api" > .env
    echo "Not in Codespaces — using /api proxy"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  TO RUN:"
echo ""
echo "  Terminal 1 (backend):"
echo "    cd backend && source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --reload"
echo ""
echo "  Terminal 2 (frontend):"
echo "    cd frontend && npm run dev"
echo ""
echo "  IMPORTANT: In the PORTS tab, set both"
echo "  port 8000 and 3000 to PUBLIC"
echo "═══════════════════════════════════════════"
