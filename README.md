# ?? Trading Signal Analyzer

> **Professional stock analysis system with async job processing, real-time progress tracking, and 12 technical indicators**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2-blue.svg)](https://reactjs.org/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)

A comprehensive stock analysis system featuring async job processing, real-time progress tracking, and 12 technical indicators for professional trading analysis.

![System Demo](docs/images/demo.gif)

## ? Key Features

- ?? **Async Job Processing** - Python threading-based background processing (no Redis required)
- ?? **12 Technical Indicators** - Trend, momentum, volatility, and volume analysis
- ?? **Real-time Progress** - Live UI updates during batch analysis
- ?? **Watchlist Management** - Track multiple stocks with latest signals
- ?? **Excel Export** - Download detailed analysis reports
- ?? **Entry/Stop/Target** - Clear trading levels for each signal
- ? **Fast & Parallel** - Process hundreds of stocks simultaneously
- ?? **Docker Ready** - Deploy anywhere with containerization

## ?? Quick Start

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/)) 
- **Node.js** (bundled in `Prerequisite/node-v20.19.5-win-x64/`)

### Installation & Running

```powershell
# 1. Run setup (first time only)
.\scripts\setup.ps1

# 2. Start backend (new window)
cd backend
.\venv\Scripts\python.exe app.py

# 3. Start frontend (new window)  
cd frontend
.\start-frontend.bat

# 4. Open browser
# http://localhost:3000
```

**That's it!** The system is ready to analyze stocks.

## ?? Documentation

| Document | Description |
|----------|-------------|
| **[START_HERE.md](START_HERE.md)** | ?? **Start here!** Complete getting started guide |
| [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md) | 5-minute quick start guide |
| [docs/guides/START_NOW.md](docs/guides/START_NOW.md) | Quick test examples |
| [docs/setup/NO_REDIS_SETUP.md](docs/setup/NO_REDIS_SETUP.md) | Threading architecture explained |
| [docs/guides/TROUBLESHOOTING.md](docs/guides/TROUBLESHOOTING.md) | Common issues and solutions |
| [docs/reference/API_TESTING.md](docs/reference/API_TESTING.md) | API endpoints reference |

**Full Documentation Index:** [docs/INDEX.md](docs/INDEX.md)

## ?? How It Works

### 1. Add Stocks to Watchlist
```javascript
// Add stocks to track
POST /watchlist
{ "symbol": "AAPL", "name": "Apple Inc." }
```

### 2. Analyze Stocks
```javascript
// Start async analysis with progress tracking
POST /analyze  
{ "tickers": ["AAPL", "MSFT", "GOOGL"], "capital": 100000 }

// Returns job_id immediately
{ "job_id": "abc-123", "status": "queued" }
```

### 3. Track Progress
```javascript
// Poll for real-time progress updates
GET /status/abc-123

// Returns live status
{ 
  "progress": 67,
  "status": "processing",
  "completed": 2,
  "total": 3
}
```

### 4. View Results
```javascript
// Get analysis results
GET /report/AAPL

// Returns complete analysis
{
  "verdict": "Strong Buy",
  "score": 0.85,
  "entry": 150.25,
  "stop_loss": 145.30,
  "target": 160.50,
  "indicators": [...12 indicators...]
}
```

## ?? Technical Indicators

### Trend Indicators (4)
- **EMA Crossover** (50/200) - Golden/Death cross signals
- **MACD** - Moving Average Convergence Divergence
- **ADX** (14) - Trend strength measurement
- **Parabolic SAR** - Stop and reverse points

### Momentum Indicators (4)
- **RSI** (14) - Relative Strength Index
- **Stochastic** - Overbought/oversold conditions
- **CCI** (20) - Commodity Channel Index
- **Williams %R** - Momentum oscillator

### Volatility Indicators (2)
- **ATR** (14) - Average True Range
- **Bollinger Bands** - Price envelope analysis

### Volume Indicators (2)
- **OBV** - On-Balance Volume
- **Chaikin Money Flow** - Volume-weighted average

## ??? Architecture

```
???????????????      ????????????????      ???????????????
?   Frontend  ????????  Flask API   ????????  Threading  ?
?   (React)   ????????   (REST)     ?      ?  (Async)    ?
???????????????      ????????????????      ???????????????
      ?                     ?                      ?
      ? Poll /status        ?                      ?
      ? every 2s            ?                      ?
      ????????????????? SQLite ????????????????????
                     ? Database
                     ?? Job Tracking
```

### Technology Stack

**Backend:**
- Python 3.13 + Flask 3.0
- SQLite (job tracking + history)
- Python threading (async processing)
- pandas, numpy, ta (technical analysis)
- yfinance (market data)

**Frontend:**
- React 18.2 + React Router
- Tailwind CSS (styling)
- Axios (HTTP client)
- Real-time polling (progress updates)

## ?? Project Structure

```
TheTool/
??? backend/                  # Python Flask API
?   ??? app.py               # Main application
?   ??? thread_tasks.py      # Background job processor  
?   ??? database.py          # SQLite operations
?   ??? indicators/          # 12 technical indicators
?   ??? utils/               # Validators & utilities
?   ??? requirements.txt     # Python dependencies
?
??? frontend/                # React web interface
?   ??? src/
?   ?   ??? pages/          # Dashboard, Analyze, Results
?   ?   ??? components/     # Reusable UI components
?   ?   ??? api/            # API client
?   ??? start-frontend.bat  # Launch script
?   ??? package.json        # Node dependencies
?
??? docs/                    # Documentation
?   ??? guides/             # User guides
?   ??? setup/              # Setup instructions
?   ??? reference/          # API & architecture docs
?
??? scripts/                 # Utility scripts
?   ??? setup.ps1           # One-time setup
?   ??? start-all.ps1       # Start all services
?   ??? check-services.bat  # Verify services
?
??? Prerequisite/            # Bundled dependencies
?   ??? node-v20.19.5-win-x64/  # Node.js (no install needed)
?
??? README.md               # This file
??? START_HERE.md           # Getting started guide
```

## ?? Usage Examples

### Analyze Single Stock
```powershell
$body = @{
    tickers = @('AAPL')
    capital = 100000
    use_demo_data = $true
} | ConvertTo-Json

$job = Invoke-RestMethod -Uri "http://localhost:5000/analyze" `
    -Method POST -Body $body -ContentType "application/json"

# Monitor progress
$jobId = $job.job_id
Invoke-RestMethod -Uri "http://localhost:5000/status/$jobId"
```

### Batch Analysis (Multiple Stocks)
```powershell
$body = @{
    tickers = @('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA')
    capital = 100000
} | ConvertTo-Json

$job = Invoke-RestMethod -Uri "http://localhost:5000/analyze" `
    -Method POST -Body $body -ContentType "application/json"

# Poll for progress
for($i=0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    $status = Invoke-RestMethod -Uri "http://localhost:5000/status/$($job.job_id)"
    Write-Host "Progress: $($status.progress)%"
    if($status.status -eq 'completed') { break }
}
```

## ?? Configuration

### Environment Variables

Create `.env` files in backend and frontend:

**backend/.env:**
```bash
DATA_PATH=./data
LOG_LEVEL=INFO
FLASK_ENV=development
```

**frontend/.env.local:**
```bash
REACT_APP_API_URL=http://localhost:5000
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
```

## ?? Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:3000
```

**docker-compose.yml** includes:
- Backend (Flask API)
- Frontend (React SPA)
- Volume mounts for data persistence

## ?? Production Deployment

In a production environment, you will need to run this application behind a reverse proxy (e.g., Nginx, Apache, or a cloud provider's load balancer). The reverse proxy should be configured to:

1.  Serve the frontend's static files (from the `frontend/build` directory).
2.  Route all requests to `/api` to the backend service on port 5000.

Here is an example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        root   /path/to/your/frontend/build;
        index  index.html;
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## ?? Performance

| Scenario | Time | Notes |
|----------|------|-------|
| Single stock (demo) | ~3-5s | Fast testing mode |
| Single stock (live) | ~10-15s | With network fetch |
| 10 stocks (parallel) | ~40-60s | Background processing |
| 100 stocks (batch) | ~5-10 min | With progress tracking |

**Scaling:**
- Threading approach: Perfect for 1-500 stocks
- For 1000+ stocks: See `docs/setup/ASYNC_JOBS_SETUP.md` for Redis + Celery setup

## ?? Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## ?? License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## ?? Acknowledgments

- **Yahoo Finance** - Market data provider
- **TradingView** - UI/UX inspiration  
- **Technical Analysis Library** - Indicator calculations

## ?? Support

- ?? **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- ?? **Issues**: [GitHub Issues](https://github.com/yourusername/thetool/issues)
- ?? **Discussions**: [GitHub Discussions](https://github.com/yourusername/thetool/discussions)

## ?? Quick Links

- [?? Getting Started Guide](START_HERE.md)
- [? 5-Minute Quickstart](docs/guides/QUICKSTART.md)
- [?? Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)
- [?? API Reference](docs/reference/API_TESTING.md)
- [??? Architecture Docs](docs/reference/ARCHITECTURE.md)
- [?? System Status](docs/guides/SYSTEM_STATUS.md)

---

**Made with ?? for traders and developers**

? Star this repo if you find it useful!
