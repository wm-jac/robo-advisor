# Repository Guidelines

## Project Structure & Module Organization

This repository contains a local robo-advisor web app with a FastAPI backend and a Next.js frontend.

- `backend/main.py` is the FastAPI entry point. It exposes `/api/analyze`, `/api/frontier`, `/api/questions`, `/api/profile`, and `/api/optimal`.
- `frontend/` contains the Next.js 14 app. `frontend/app/page.tsx` redirects to `/funds`; the main routes are `/funds`, `/frontier`, `/profile`, and `/portfolio`.
- `frontend/lib/api.ts` is the frontend API client. It defaults to `http://localhost:8000` and can be overridden with `NEXT_PUBLIC_API_BASE_URL`.
- `frontend/lib/store.ts` holds shared client state with Zustand.
- `frontend/lib/i18n.ts` contains frontend translations and profile/question localisation.
- `frontend/components/` contains reusable UI components such as charts, metric cards, sidebar, and top bar.
- `src/data_loader.py` parses FSMOne-style CSVs, aligns price series, computes returns, annualised statistics, normalised prices, and standalone fund stats.
- `src/portfolio.py` computes the efficient frontier, GMVP, and portfolio statistics.
- `src/optimizer.py` maximises mean-variance utility and produces allocation sensitivity analysis.
- `src/risk_assessment.py` defines the questionnaire, score range, risk-aversion mapping, investor profile labels, and utility function.
- `src/risk_free_rate.py` fetches and parses the MAS 1-year T-bill yield used as the Sharpe ratio risk-free rate. `backend/main.py` caches that rate for API responses and falls back to `0.0` only when the MAS fetch fails.
- `scripts/download_fsmone_funds.py` downloads the default FSMOne fund basket into `data/`. The current default basket includes `FI3107 - Fidelity Global Technology A-ACC SGD`.
- `data/` stores local CSV inputs for the default analysis path. Generated CSV files are ignored by Git.
- `requirements.txt` lists backend and shared Python dependencies. `frontend/package.json` lists frontend dependencies and scripts.

There is no `app.py` Streamlit entry point in the current implementation.

## Build, Test, and Development Commands

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Download the default FSMOne fund basket into `data/`:

```bash
python3 scripts/download_fsmone_funds.py
```

Check the planned downloads without writing CSVs:

```bash
python3 scripts/download_fsmone_funds.py --dry-run
```

Run the backend locally:

```bash
python3 -m uvicorn backend.main:app --reload --port 8000
```

Run the frontend in stable preview mode:

```bash
cd frontend
npm run preview
```

Use hot reload while actively editing frontend code:

```bash
cd frontend
npm run dev
```

Run backend syntax checks:

```bash
python3 -m compileall backend src scripts
```

Run a frontend production build:

```bash
cd frontend
npm run build
```

## Data Flow

The frontend starts at `/funds` and auto-loads default CSV data from `data/` through `/api/analyze` when no files are uploaded. Uploaded CSVs override the local data for that request.

`/api/analyze` loads and normalises fund prices, computes log returns, annualised mean returns and covariance, standalone statistics, correlation data, date-range metadata, and risk-free-rate metadata. Standalone Sharpe ratios use excess return over the cached MAS 1-year T-bill rate.

`/api/frontier` computes efficient frontiers and GMVP results for long-only or short-selling cases.

`/api/questions` returns the risk questionnaire and score bounds. `/api/profile` maps the submitted score to risk aversion `A` and an investor profile.

`/api/optimal` maximises utility for the chosen `A`, short-selling setting, and fund universe. It returns portfolio metrics, allocation rows, sensitivity analysis across nearby `A` values, and risk-free-rate metadata. The optimisation objective still uses nominal expected return, while the reported Sharpe ratio uses excess return over the cached MAS 1-year T-bill rate.

## Coding Style & Naming Conventions

Use Python with 4-space indentation, type hints where they clarify contracts, and `snake_case` for functions and variables. Keep API request/response handling in `backend/main.py`; keep reusable finance logic in `src/`.

Use TypeScript for frontend code. Keep route-level UI in `frontend/app/*/page.tsx`, shared components in `frontend/components/`, API calls in `frontend/lib/api.ts`, global client state in `frontend/lib/store.ts`, and translations in `frontend/lib/i18n.ts`.

Preserve the current API response shapes unless you update every frontend consumer at the same time. Values sent to the frontend should be JSON-safe; backend helpers currently convert NumPy scalars and NaN values before returning responses.

For fund data changes, update the downloader defaults and aliases together so fund names resolve by stable FSMOne code. The default basket should remain suitable for automatic loading from `data/`.

## Testing Guidelines

No dedicated automated test suite is configured yet. When adding tests, prefer `pytest` for Python and place tests under `tests/` with names such as `test_data_loader.py`, `test_portfolio.py`, or `test_optimizer.py`.

Prioritise deterministic tests for CSV parsing, return calculations, covariance regularisation, optimiser constraints, short-selling behaviour, risk-score mapping, and API response shapes.

Until tests are added, use these verification steps for relevant changes:

```bash
python3 -m compileall backend src scripts
cd frontend
npm run build
```

For end-to-end checks, run the backend on port `8000`, run the frontend on port `3000`, then exercise the `/funds -> /frontier -> /profile -> /portfolio` workflow with local data and at least one CSV upload path when data loading changes.

## Commit & Pull Request Guidelines

Use concise, imperative commit messages, for example `Update default fund basket` or `Fix frontier chart ranges`.

Pull requests should include a short description, verification commands, screenshots for visible UI changes, and notes about any changes to API shapes, CSV expectations, optimiser assumptions, or default fund selection.

## Security & Configuration Tips

Do not commit `.venv/`, `frontend/node_modules/`, `frontend/.next/`, local cache files, or generated CSV downloads. These are already covered by `.gitignore`.

The app currently requires no secrets. If configuration is added later, use environment variables and document them in `README.md` and this file.

Network-dependent commands include the FSMOne downloader and MAS risk-free-rate fetcher. Use `--dry-run` for downloader resolution checks when CSV output is not needed.
