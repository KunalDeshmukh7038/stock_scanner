# Sentimental Drive Frontend

React + Tailwind frontend for the FastAPI stock analysis backend.

## Prerequisites

- Node.js 18+
- npm 9+
- FastAPI backend running at `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

Optional environment file:

```bash
cp .env.example .env
```

## Pages

- `/` home dashboard
- `/stocks/:symbol` stock detail workspace
- `/screener` filterable stock screener
