# TheTool Distribution - Minimal Package

This is a **minimal distribution** of TheTool containing only essential files needed to run the stock analysis application.

## What's Included

### Core Application Files
- ? Backend Python code (Flask API, indicators, utilities)
- ? Frontend React code (UI, components, pages)
- ? Database initialization scripts
- ? NSE stocks data (2,192 stocks)
- ? Configuration files
- ? Startup scripts

### NOT Included (to keep package small)
- ? Node.js binaries (you need to install separately)
- ? Python virtual environment (created during setup)
- ? node_modules folder (installed during setup)
- ? Test files and documentation (see original package)
- ? Docker configuration
- ? Celery/Redis setup (optional, for advanced users)

---

## Quick Start

### 1. Prerequisites
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))

### 2. Run Setup
```powershell
.\setup.ps1
```

### 3. Start Application
Double-click:
- `start-backend.bat`
- `start-frontend.bat`

### 4. Open Browser
http://localhost:3000

---

## File Size Comparison

**Full Package:** ~150 MB (with Node.js, venv, node_modules, docs)
**This Package:** ~5 MB (source code only)
**After Setup:** ~120 MB (with installed dependencies)

---

## What Gets Installed During Setup

- **Python packages** (~50 MB): Flask, pandas, yfinance, etc.
- **Node packages** (~200 MB): React, Tailwind, build tools
- **Virtual environment** (~30 MB): Isolated Python environment
- **SQLite database** (~1 MB): Stock data and analysis results

---

## Support

For detailed documentation, see the **full TheTool package** which includes:
- 15+ documentation files
- Setup guides
- Troubleshooting help
- API documentation
- Architecture details

---

## Package Contents

```
TheTool-Distribution/
??? backend/
?   ??? app.py                  # Main Flask server
?   ??? database.py             # Database setup
?   ??? thread_tasks.py         # Background jobs
?   ??? requirements.txt        # Python dependencies
?   ??? .env.example           # Configuration template
?   ??? indicators/             # 12 technical indicators
?   ?   ??? adx.py
?   ?   ??? atr.py
?   ?   ??? bollinger.py
?   ?   ??? cci.py
?   ?   ??? cmf.py
?   ?   ??? ema.py
?   ?   ??? macd.py
?   ?   ??? obv.py
?   ?   ??? psar.py
?   ?   ??? rsi.py
?   ?   ??? stochastic.py
?   ?   ??? williams.py
?   ??? utils/                  # Helper functions
?       ??? compute_score.py
?       ??? data_validator.py
?       ??? entry_calculator.py
?       ??? fetch_data.py
?       ??? logger.py
?       ??? risk_manager.py
?
??? frontend/
?   ??? src/
?   ?   ??? pages/
?   ?   ?   ??? Dashboard.js           # Personal watchlist
?   ?   ?   ??? AllStocksAnalysis.js   # Bulk analysis (2500 stocks)
?   ?   ?   ??? Results.js             # Analysis reports
?   ?   ??? components/
?   ?   ?   ??? NavigationBar.js
?   ?   ?   ??? Header.js
?   ?   ?   ??? AddStockModal.js
?   ?   ??? api/
?   ?   ?   ??? api.js                 # API client
?   ?   ??? App.js
?   ?   ??? index.js
?   ?   ??? index.css
?   ??? public/                         # Static assets
?   ??? package.json                    # Node dependencies
?   ??? tailwind.config.js
?   ??? postcss.config.js
?
??? data/
?   ??? nse_stocks.csv          # 2,192 Indian stocks
?
??? setup.ps1                   # Automated setup script
??? start-backend.bat           # Start Flask server
??? start-frontend.bat          # Start React app
??? SETUP_AND_RUN.md           # Quick setup guide
??? START_HERE.md              # Original documentation
??? README.md                  # This file
```

---

## Features

- ? Analyze 2,500+ stocks
- ? 12 technical indicators
- ? Real-time progress tracking
- ? Historical analysis (last 10 per stock)
- ? Excel export
- ? Modern UI with Tailwind CSS
- ? Background job processing (Python threading)

---

## License

Same as original TheTool project.

---

**Ready to start? Run `.\setup.ps1`**
