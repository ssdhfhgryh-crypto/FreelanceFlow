# FreelanceFlow

A lightweight freelance productivity dashboard built with Python, Streamlit, Pandas, and SQLite.

## Features

- Create and manage freelance projects
- Record work sessions and notes
- Estimate earnings from hours × hourly rate
- Track whether logged work has been paid
- View dashboard metrics and project earnings charts
- Filter reports by month and export records to CSV

## Quick start

Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser. The SQLite database (`freelanceflow.db`) is created automatically beside `app.py` when you first run the app.

## Project structure

```text
FreelanceFlow/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Important notes

- Earnings are estimates calculated from the hourly rate and hours entered by the user.
- Payment status is manually entered; this MVP does not connect to payment providers or freelance platforms.
- Data is stored locally in SQLite and is not encrypted by this prototype.
- Do not enter passwords, API keys, or sensitive client data.

## Roadmap

- Add automated tests for earnings calculations
- Add CSV import and input validation
- Add configurable currencies
- Add optional AI summaries after the core app is stable
- Consider user authentication and hosted database before any public multi-user deployment

## Development with AI coding assistants

Claude Code or another coding assistant can help implement roadmap items. Review changes, run the app, test edge cases, and understand the code before accepting changes.
