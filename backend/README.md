# Sentimental Drive Backend

FastAPI backend for the React frontend.

## Install

```bash
cd C:\Users\admin\Desktop\Sentimental_Drive_Stock
pip install -r backend\requirements.txt
```

## Run

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoints

- `GET /api/market`
- `GET /api/stocks`
- `GET /api/stocks/{symbol}`
- `GET /api/top-picks`

## Optional

Set `NEWSAPI_KEY` in your environment if you want richer news sentiment in stock detail responses.

## Angel One Live Data

1. Copy the template file:

```bash
copy .env.example .env
```

2. Open `.env` and add your Angel One credentials:

- `ANGEL_API_KEY`
- `ANGEL_CLIENT_CODE`
- `ANGEL_PIN`
- `ANGEL_TOTP_SECRET`

3. Restart the backend.

When these values are present, the backend will try to use Angel One SmartAPI for:

- `/api/market` live Indian indices
- `/api/stocks` live stock prices and day change
- `/api/stocks/{symbol}` live stock price refresh

If Angel One is not configured or temporarily fails, the backend falls back to the current cached CSV / Yahoo Finance flow so the app still opens.
