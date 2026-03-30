# BC Admissions Email Assistant — Frontend

React frontend for the Brooklyn College Admissions Email Response Generator.

## Setup

```bash
# 1. Navigate to frontend folder
cd frontend

# 2. Install dependencies
npm install

# 3. Start dev server (make sure backend is running on port 8000)
npm run dev
```

The frontend will be running at `http://localhost:3000`

The Vite config automatically proxies `/api` requests to the backend at `http://localhost:8000`.

## Build for Production

```bash
npm run build
```

Output will be in the `dist/` folder, ready to deploy to Vercel or any static host.
