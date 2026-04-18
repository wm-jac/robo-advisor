# Repository Guidelines

## Project Structure & Module Organization

This repository contains a local Streamlit robo-advisor app.

- `app.py` is the Streamlit entry point and UI orchestration layer.
- `src/data_loader.py` loads FSMOne-style fund CSVs and computes return inputs.
- `src/portfolio.py` contains efficient frontier and GMVP calculations.
- `src/optimizer.py` contains utility-maximising portfolio optimisation.
- `src/risk_assessment.py` defines the questionnaire and risk-aversion mapping.
- `data/README.md` documents expected fund CSV format. The current app loads CSVs through the sidebar uploader, not automatically from `data/`.
- `requirements.txt` lists Python dependencies.

There is currently no dedicated `tests/` directory. Add one when introducing automated tests.

## Build, Test, and Development Commands

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app locally:

```bash
python -m streamlit run app.py
```

Run a syntax check:

```bash
python -m compileall app.py src
```

## Coding Style & Naming Conventions

Use Python with 4-space indentation and clear, descriptive names. Keep UI code in `app.py`; place reusable financial logic in `src/` modules. Prefer `snake_case` for functions and variables, `UPPER_CASE` for constants, and short module-level docstrings for files with non-obvious responsibilities.

Keep functions focused: data parsing belongs in `data_loader.py`, optimisation routines in `optimizer.py`, portfolio statistics in `portfolio.py`, and questionnaire logic in `risk_assessment.py`.

## Testing Guidelines

No test framework is configured yet. For new tests, use `pytest` and place files under `tests/` with names such as `test_data_loader.py` or `test_optimizer.py`. Prioritise deterministic unit tests for CSV parsing, return calculations, constraints, and risk-score mapping. Until tests exist, run `python -m compileall app.py src` and manually exercise the Streamlit workflow with at least two valid CSV uploads.

## Commit & Pull Request Guidelines

The current history only shows `Initial commit: BMD5302 Robo-Advisor`, so no detailed convention is established. Use concise, imperative commit messages, for example `Add CSV validation checks` or `Fix long-only optimiser weights`.

Pull requests should include a short description, test or manual verification steps, screenshots for visible UI changes, and notes about any changes to CSV format expectations or optimisation assumptions.

## Security & Configuration Tips

Do not commit `.venv/`, uploaded fund CSVs containing sensitive data, or local Streamlit cache files. This app does not require API keys or secrets in its current form.
