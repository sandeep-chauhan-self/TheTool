# TheTool - Quick Setup Guide

## Prerequisites

- **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 18+** installed ([Download](https://nodejs.org/))
- Internet connection (for package installation and stock data)

---

## Step 1: Setup (First Time Only)

Open PowerShell in this folder and run:

```powershell
.\setup.ps1
```

**What this does:**
- Creates Python virtual environment
- Installs all Python packages (Flask, yfinance, pandas, etc.)
- Installs all React packages
- Initializes SQLite database

**Time:** 3-5 minutes

---

## Step 2: Start the Application

### Option A: Using Batch Files (Easiest)

Double-click these files in Windows Explorer:
1. **`start-backend.bat`** (starts Python Flask server)
2. **`start-frontend.bat`** (starts React app)

Wait 30 seconds, then browser opens automatically at http://localhost:3000

> **Note:** If `npm start` doesn't work in the batch files, the command will automatically fall back to `npx react-scripts start`.

### Option B: Manual Commands

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\python.exe app.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npx react-scripts start
```

---

## Step 3: Use the Application

1. **Add stocks** to your watchlist (e.g., `AAPL`, `MSFT`, `INFY.NS`)
2. **Select stocks** using checkboxes
3. **Click "Analyze Selected Stocks"**
4. **View results** - See Buy/Sell signals and download reports

---

## Stock Ticker Formats

- **US Stocks:** `AAPL`, `MSFT`, `GOOGL`, `TSLA`
- **Indian NSE Stocks:** Add `.NS` ? `INFY.NS`, `TCS.NS`, `RELIANCE.NS`

---

## Features

? Analyze 2,500+ stocks with one click
? 12 technical indicators (RSI, MACD, Bollinger, etc.)
? Real-time progress tracking
? Historical analysis (last 10 runs per stock)
? Excel export reports
? Clean, modern UI

---

## Troubleshooting

### Port Already in Use

If you see "Port 5000 already in use":

```powershell
# Find and kill the process
Get-Process -Name python | Stop-Process -Force
```

### Module Not Found

```powershell
cd backend
python -m pip install -r requirements.txt
```

### react-scripts Not Found

If you see "react-scripts is not found" or similar errors:

```powershell
cd frontend
npm install
```

Then use `npx react-scripts start` instead of `npm start`

### Frontend Won't Start

```powershell
cd frontend
npm install
npx react-scripts start
```

---

## What's Included

```
TheTool-Distribution/
??? backend/               # Python Flask API
?   ??? app.py            # Main server
?   ??? database.py       # SQLite database
?   ??? thread_tasks.py   # Background jobs
?   ??? indicators/       # 12 technical indicators
?   ??? utils/            # Helper functions
?   ??? requirements.txt  # Python packages
?
??? frontend/             # React app
?   ??? src/
?   ?   ??? pages/       # Dashboard, All Stocks, Results
?   ?   ??? components/  # UI components
?   ?   ??? api/         # API client
?   ??? package.json     # Node packages
?
??? data/
?   ??? nse_stocks.csv   # 2,192 Indian stocks
?
??? setup.ps1            # One-time setup script
??? start-backend.bat    # Start Flask server
??? start-frontend.bat   # Start React app
```

---

## Need Help?

- Check **START_HERE.md** for detailed documentation
- Check **README.md** for technical details
- All documentation included in original TheTool folder

---

**Ready?** Run `.\setup.ps1` to begin!
