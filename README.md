# Robo-Advisor

This project includes:

- a Next.js frontend in `frontend/`
- a FastAPI backend in `backend/`
- portfolio / risk logic in `src/`
- optional local fund CSVs in `data/`

## 1. Clone the repo

```bash
git clone https://github.com/wm-jac/robo-advisor.git
cd robo-advisor
```

## 2. Set up Python

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## 3. Set up the frontend

Install Node dependencies:

```bash
cd frontend
npm install
cd ..
```

## 4. Load fund data

You can either:

- place compatible CSV files in `data/`, or
- let the app use uploaded CSVs from the UI

To download the default project basket into `data/`:

```bash
python3 scripts/download_fsmone_funds.py
```

To download specific funds:

```bash
python3 scripts/download_fsmone_funds.py FI3095 JPM048 --start-date 2021-01-01 --end-date 2025-12-31
python3 scripts/download_fsmone_funds.py --identifier "Fidelity America A-SGD (hedged)"
```

More data notes are in [data/README.md](data/README.md).

## 5. Start the backend

Open Terminal 1:

```bash
cd /path/to/robo-advisor
source .venv/bin/activate
python3 -m uvicorn backend.main:app --reload --port 8000
```

The API will run at:

```text
http://127.0.0.1:8000
```

## 6. Start the frontend

Open Terminal 2:

```bash
cd /path/to/robo-advisor/frontend
npm run preview
```

The frontend will run at:

```text
http://localhost:3000
```

`npm run preview` is the recommended mode for demos / stable refreshes.

If you are actively editing the frontend and want hot reload instead:

```bash
npm run dev
```

## 7. Open the app

Go to:

```text
http://localhost:3000
```

## Notes

- The frontend expects the backend on port `8000`.
- If `data/` already contains the fund CSVs, the app can load them automatically.
- If no local data is present, you can still upload CSVs through the frontend.
- Generated CSV files in `data/` are ignored by Git.

## Quick restart

Backend:

```bash
cd /path/to/robo-advisor
source .venv/bin/activate
python3 -m uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd /path/to/robo-advisor/frontend
npm run preview
```
