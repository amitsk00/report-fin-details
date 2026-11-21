# ExpensePulse — Personal Expense & Pattern Analyzer

A full-stack personal finance application with a Python & pandas backend and an interactive modern web frontend. It reads transaction CSV files, maintains them in memory as an enriched DataFrame, and provides multidimensional filtering (by Label/Person, Account, Category, Type, Date, Nature) along with in-depth expense pattern analytics.

---

## Architecture Overview

```
d:\sandbox\report-fin\
├── requirements.txt       # Project dependencies (Flask, pandas, numpy, tabulate, etc.)
├── venv/                  # Local isolated Python 3.14 virtual environment
├── config.ini             # Path and pattern configuration for expense CSVs
├── expense_reader.py      # Core DataFrame manager: file discovery, parsing, label cleaning & filtering
├── expense_analytics.py   # Pattern recognition engine (Weekday, Weekly, Category, Account, Label reports)
├── app.py                 # Flask REST API and web application server
├── run.py                 # Convenient startup runner (opens browser automatically)
├── run_app.bat            # Windows 1-click batch launcher
├── templates/
│   └── index.html         # Modern responsive frontend (Tailwind CSS, Chart.js, FontAwesome)
└── test_app.py            # Unit and integration test suite
```

---

## Key Features

### 1. Robust Python Backend & DataFrame Management (`expense_reader.py`)
- Reads file settings directly from `config.ini` (`filePath`, `fileName`, `daysInPast`).
- Recursively discovers and loads all matching monthly CSV files (over 6,400+ transactions supported).
- Standardizes columns (`Title`, `Expenses`, `Category Group`, `Account`, `Date`).
- **Smart Label Cleaning & Extraction**: Cleans app prefixes (`0 Amit 0 Dipti` &rarr; `Amit`, `Dipti`) and maintains both token lists and cleaned strings for multi-tag filtering.
- **Derived Analytical Features**: Computes `YearMonth`, `Year`, `Month`, `Weekday` (Monday–Sunday), `Weekend` vs `WeekDay`, `WeekNum` (ISO weeks), `is_recurring`, `is_excluded` (EMI), and `is_discretionary`.
- High-speed in-memory filtering across any combination of dimensions.

### 2. Multi-Dimensional Interactive Filtering
- **Labels / People**: Multi-select pills with search (e.g. `Amit`, `Dipti`, `Family`, `Adi`, `Donation`, `Health`, etc.).
- **Accounts**: Checkboxes for all accounts (`AmitK Savings`, `AmitK CC`, `Sodexho`, `Wallet`, `Dipti Savings`, etc.).
- **Categories & Groups**: Dropdown filters for Category Groups (`Household`, `Entertainment`, `Essentials`, `Travel`) and individual Categories (`Grocery`, `Dining Out`, `FoodDelivery`, `Monthly`, etc.).
- **Transaction Type**: Quick segment toggle (`Expense`, `Income`, `All`).
- **Date Periods**: 1-click presets (`All Time`, `Last 90 Days`, `Year 2026`, `Year 2025`) or custom Start & End date pickers.
- **Spending Nature**: Filter by `Discretionary (Day-to-day)`, `Recurring (Bills/Staff)`, or `Large / EMI`.
- **Day Type**: Filter by `Weekend Only` (Sat–Sun) or `Weekday Only` (Mon–Fri).
- **Text Search & Amount Limits**: Instant title/notes search and min/max amount limits.

### 3. Expense Pattern Analytics & Reports (`expense_analytics.py`)
- **Monthly Income vs Expense & Savings**: Bar + line trend showing monthly income, expenses, net savings, and savings rate %.
- **Weekday Spending Pattern**: Identifies which days of the week have the highest expenditure and compares weekend vs weekday burn rates.
- **Weekly Run-Rate Progression**: Analyzes week-by-week spending cadence and projects monthly run rate (`Weekly Mean * 4.33`).
- **Category Matrix (Pivot Heatmap)**: Complete matrix of monthly spend per category with totals and percentages.
- **Account Distribution**: Breakdown of spending across payment methods (Credit cards, savings accounts, meal cards, wallets).
- **Label / Person Distribution**: Visualizes spending allocated to specific family members or personal goals.
- **Label Deep Dive (Category & Account Level Analysis)**: Dedicated tab to focus on any selected label (e.g. `Amit`, `Dipti`, `Family`, `Adi`) and dissect spending at both the Category level (shopping, dining, medicines, groceries) and Account level (savings accounts, credit cards, Sodexho, wallet), including month-by-month category heatmaps and individual item purchases.
- **Spreadsheet / XLS-Ready Report**: Generates recurring, EMI, and weekend spending tables formatted with 1-click "Copy for Excel" buttons matching your legacy workflow.

### 4. Interactive Data Explorer
- Paginated table with custom page sizes (15, 25, 50, 100).
- Real-time column sorting (Date, Title, Amount, Category, Account).
- Color-coded amounts and labeled tag badges.
- 1-click **Export Filtered CSV** to download the exact filtered view.

---

## Package Management & Environment

Dependencies are defined in [`requirements.txt`](file:///d:/sandbox/report-fin/requirements.txt):
- `Flask>=3.0.0`
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `tabulate>=0.9.0`
- `configparser>=5.0.0`

The project has its own dedicated, isolated virtual environment in [`venv/`](file:///d:/sandbox/report-fin/venv).

To install or update dependencies:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Or directly:
```powershell
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
```

---

## How to Run

### Method 1: Double-click Batch File
Double-click [`run_app.bat`](file:///d:/sandbox/report-fin/run_app.bat) in Windows Explorer or run:
```cmd
.\run_app.bat
```

### Method 2: Command Line
Using the project's local virtual environment:
```powershell
& ".\venv\Scripts\python.exe" run.py
```
Or after activating the venv:
```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

The application will start at:
```
http://127.0.0.1:5000
```

---

## Running the Automated Test Suite

To run the unit and integration tests using the local environment:
```powershell
& ".\venv\Scripts\python.exe" -m unittest test_app.py
```
All 9 test cases will verify metadata extraction, filtering, pattern calculations, CSV export, and HTML rendering.
# report-fin-details
