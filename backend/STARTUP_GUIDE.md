# Backend Startup Guide

## Quick Start

### Option 1: PowerShell (Recommended)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

### Option 2: Command Prompt
```cmd
cd backend
venv\Scripts\activate.bat
python app.py
```

### Option 3: From Project Root
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

## What Happens When Starting

1. **Virtual Environment Activates**
   - Prompt changes to `(venv) PS C:\...\backend>`
   - Isolated Python environment loaded

2. **Database Initializes**
   ```
   Database initialized successfully
   ```

3. **Background Scheduler Starts**
   ```
   [2025-11-13 10:41:53] [INFO] Background scheduler started
   ```

4. **Flask Server Starts**
   ```
   * Serving Flask app 'app'
   * Debug mode: on
   * Running on http://127.0.0.1:5000
   * Running on http://0.0.0.0:5000
   Press CTRL+C to quit
   ```

5. **Debugger Ready**
   ```
   * Debugger is active!
   * Debugger PIN: 138-603-170
   ```

## Verify Backend is Running

### Test Health Endpoint
```powershell
# PowerShell
Invoke-WebRequest http://localhost:5000/health

# Or use browser
# Navigate to: http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T10:41:53.123456"
}
```

## Common Issues

### "python: command not found"
**Solution**: Python not in PATH
```powershell
# Use full path
C:\Python311\python.exe app.py

# Or reinstall Python with "Add to PATH" checked
```

### "No module named 'flask'"
**Solution**: Virtual environment not activated or dependencies not installed
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Then run
python app.py
```

### "Address already in use" / Port 5000 busy
**Solution**: Another process using port 5000
```powershell
# Find process on port 5000
netstat -ano | findstr :5000

# Kill the process
taskkill /PID <PID> /F

# Or use different port
$env:FLASK_RUN_PORT=5001
python app.py
```

### "Database is locked"
**Solution**: Another instance accessing database
```powershell
# Stop all backend instances
# Delete database and reinitialize
rm data\trading_signals.db
python -c "from database import init_db; init_db()"
```

### Import errors after setup
**Solution**: Reinstall dependencies
```powershell
pip install --force-reinstall -r requirements.txt
```

## Configuration

### Environment Variables (.env)
```env
# Flask settings
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Server settings
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000

# Database
DATABASE_PATH=data/trading_signals.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Data fetching
CACHE_EXPIRY_HOURS=24
MAX_WORKERS=10

# Background jobs
NSE_UPDATE_HOUR=6
CACHE_CLEAN_HOUR=3
LOG_COMPRESS_DAY=0
```

### Modify in code (app.py)
```python
if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',  # Allow external connections
        port=5000,       # Change port here
        threaded=True    # Handle multiple requests
    )
```

## API Endpoints

### Health Check
```
GET /health
```

### Analyze Stock
```
POST /analyze
Body: {"ticker": "AAPL", "indicators": ["rsi", "macd"]}
```

### Check Analysis Status
```
GET /status/<job_id>
```

### Get Analysis Report
```
GET /report/<ticker>
```

### Download Excel Report
```
GET /report/<ticker>/download
```

### Watchlist Management
```
GET /watchlist
POST /watchlist
DELETE /watchlist?symbol=AAPL
```

### Get Configuration
```
GET /config
```

### NSE Universe
```
GET /nse
```

See [API_TESTING.md](../API_TESTING.md) for complete API documentation.

## File Structure

```
backend/
??? app.py                 # Main Flask application
??? database.py            # Database setup
??? requirements.txt       # Python dependencies
??? .env                   # Environment variables
??? .env.example           # Template for .env
??? Dockerfile             # Container config
??? test_installation.py   # Installation test
??? indicators/            # 12 indicator modules
?   ??? rsi.py
?   ??? macd.py
?   ??? adx.py
?   ??? psar.py
?   ??? ema.py
?   ??? stochastic.py
?   ??? cci.py
?   ??? williams.py
?   ??? atr.py
?   ??? bollinger.py
?   ??? obv.py
?   ??? cmf.py
??? utils/                 # Utility modules
?   ??? logger.py          # Logging setup
?   ??? fetch_data.py      # Yahoo Finance client
?   ??? compute_score.py   # Scoring algorithm
?   ??? cron_tasks.py      # Background jobs
??? data/                  # Data storage
?   ??? cache/             # Cached market data
?   ??? reports/           # Generated reports
?   ??? trading_signals.db # SQLite database
??? logs/                  # Application logs
?   ??? app.log
??? venv/                  # Virtual environment
```

## Background Jobs

### Scheduled Tasks (cron_tasks.py)

1. **NSE Universe Update**
   - Runs: Daily at 6:00 AM
   - Updates list of NSE stocks

2. **Cache Cleanup**
   - Runs: Daily at 3:00 AM
   - Removes data older than 24 hours

3. **Log Compression**
   - Runs: Weekly on Sunday
   - Compresses old log files

### Manual Job Triggers
```python
from utils.cron_tasks import update_nse_universe, cleanup_old_cache

# Update NSE list now
update_nse_universe()

# Clean cache now
cleanup_old_cache()
```

## Development Tips

### Enable Debug Mode
Already enabled in `app.py`:
```python
app.run(debug=True)
```

Benefits:
- Auto-restart on code changes
- Detailed error pages
- Interactive debugger

### View Logs
```powershell
# Tail logs in real-time
Get-Content logs\app.log -Wait -Tail 50

# Or use notepad
notepad logs\app.log
```

### Test Indicators
```python
python -c "from indicators.rsi import analyze_rsi; print(analyze_rsi('AAPL'))"
```

### Database Queries
```python
python
>>> from database import get_db_connection
>>> conn = get_db_connection()
>>> cursor = conn.cursor()
>>> cursor.execute("SELECT * FROM watchlist").fetchall()
```

### Clear Cache
```powershell
Remove-Item data\cache\* -Recurse
```

## Performance Tuning

### Parallel Processing
Configured in `app.py`:
```python
executor = ThreadPoolExecutor(max_workers=10)
```

Increase for more concurrent analysis:
```python
executor = ThreadPoolExecutor(max_workers=20)
```

### Cache Duration
Modify in `utils/fetch_data.py`:
```python
CACHE_EXPIRY_HOURS = 24  # Change to 48 for 2 days
```

### Logging Level
In `.env`:
```env
LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR
```

## Production Deployment

### Using Gunicorn (Linux/macOS)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Waitress (Windows)
```powershell
pip install waitress
waitress-serve --listen=*:5000 app:app
```

### Using Docker
```powershell
docker build -t trading-analyzer-backend .
docker run -p 5000:5000 trading-analyzer-backend
```

## Security Considerations

### For Production:
1. Disable debug mode:
   ```python
   app.run(debug=False)
   ```

2. Set secret key:
   ```python
   app.secret_key = 'your-secret-key-here'
   ```

3. Enable HTTPS
4. Rate limiting
5. Input validation
6. Authentication

## Troubleshooting Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Python 3.11+ version
- [ ] Port 5000 available
- [ ] Database initialized
- [ ] Required directories exist (data/, logs/)
- [ ] Internet connection for market data

## Next Steps

1. **Verify Backend Running**
   ```powershell
   curl http://localhost:5000/health
   ```

2. **Test Analysis**
   ```powershell
   curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d '{"ticker":"AAPL"}'
   ```

3. **Start Frontend**
   ```powershell
   cd ..\frontend
   .\start-frontend.bat
   ```

4. **Open Browser**
   http://localhost:3000

## Need Help?

- See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- Check [API_TESTING.md](../API_TESTING.md)
- Review logs in `logs/app.log`
- Test installation: `python test_installation.py`
