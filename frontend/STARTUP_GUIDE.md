# Frontend Startup Guide

## Quick Start

### Option 1: Using Batch File (Recommended)
```bash
cd frontend
.\start-frontend.bat
```
This automatically:
- Sets up Node.js path
- Starts React development server
- Opens browser at http://localhost:3000

### Option 2: Manual PowerShell
```powershell
cd frontend
$env:Path = "..\Prerequisite\node-v20.19.5-win-x64;" + $env:Path
npm start
```

### Option 3: From Project Root
```powershell
# From TheTool directory
cd frontend
.\start-frontend.bat
```

## What Happens When Starting

1. **Node.js Detection**
   - Batch file adds bundled Node.js to PATH
   - No system-wide Node.js installation needed

2. **React Compilation**
   - Webpack compiles JavaScript/JSX
   - Tailwind CSS processes styles
   - Takes 10-30 seconds on first run

3. **Development Server Starts**
   - Server runs on http://localhost:3000
   - Hot reload enabled (auto-refresh on code changes)
   - Browser opens automatically

4. **Expected Output**
   ```
   Compiled successfully!

   You can now view trading-analyzer-frontend in the browser.

     Local:            http://localhost:3000
     On Your Network:  http://192.168.x.x:3000

   Note that the development build is not optimized.
   To create a production build, use npm run build.
   ```

## Common Issues

### "npm: command not found"
**Solution**: The bundled Node.js isn't in PATH
```powershell
# Run from frontend directory
.\start-frontend.bat
```

### "Port 3000 already in use"
**Solution**: Another app is using port 3000
```powershell
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use different port
set PORT=3001 && npm start
```

### "Cannot find module 'react-scripts'"
**Solution**: Dependencies not installed
```powershell
cd frontend
..\Prerequisite\node-v20.19.5-win-x64\npm.cmd install
```

### Browser doesn't open automatically
**Solution**: Manually open http://localhost:3000

### Compilation errors after code changes
**Solution**: 
1. Stop server (Ctrl+C)
2. Delete build cache: `rm -r node_modules/.cache`
3. Restart: `.\start-frontend.bat`

## Development Tips

### Hot Reload
- Edit any file in `src/`
- Save the file
- Browser auto-refreshes (no restart needed)

### See Console Logs
- Open browser DevTools (F12)
- Go to Console tab
- See `console.log()` outputs

### Check Network Requests
- Open DevTools (F12)
- Go to Network tab
- See all API calls to backend

### Disable Auto Browser Open
```powershell
# In frontend/.env
BROWSER=none
```

## Production Build

### Create Optimized Build
```powershell
cd frontend
..\Prerequisite\node-v20.19.5-win-x64\npm.cmd run build
```

This creates:
- `build/` folder with optimized files
- Minified JavaScript
- Compressed CSS
- Optimized images

### Serve Production Build
```powershell
npm install -g serve
serve -s build -p 3000
```

Or use backend to serve:
```python
# In backend/app.py
app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
```

## File Structure

```
frontend/
??? public/               # Static files
?   ??? index.html       # HTML template
?   ??? favicon.ico      # Browser icon
??? src/
?   ??? App.js           # Main component with routing
?   ??? index.js         # Entry point
?   ??? index.css        # Global styles + Tailwind
?   ??? pages/           # Page components
?   ?   ??? Dashboard.js
?   ?   ??? AnalysisConfig.js
?   ?   ??? Results.js
?   ??? components/      # Reusable components
?   ?   ??? Header.js
?   ?   ??? AddStockModal.js
?   ??? api/
?       ??? api.js       # API client for backend
??? package.json         # Dependencies
??? tailwind.config.js   # Tailwind CSS config
??? postcss.config.js    # PostCSS config
??? start-frontend.bat   # Startup script
??? README.md            # Frontend docs

```

## Available Scripts

### `npm start`
Runs development server with hot reload

### `npm run build`
Creates production-optimized build

### `npm test`
Runs test suite (if configured)

### `npm run eject`
?? **Warning**: One-way operation. Exposes webpack config.

## Environment Variables

Create `frontend/.env`:
```env
# Backend API URL
REACT_APP_API_URL=http://localhost:5000

# Disable browser auto-open
BROWSER=none

# Custom port
PORT=3001
```

Access in code:
```javascript
const apiUrl = process.env.REACT_APP_API_URL;
```

## Connecting to Backend

Frontend expects backend at `http://localhost:5000`

**API Client**: `src/api/api.js`
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

**CORS must be enabled** in backend (already configured):
```python
# backend/app.py
CORS(app)  # Allows requests from localhost:3000
```

## Next Steps

1. **Start Backend First**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python app.py
   ```

2. **Then Start Frontend**
   ```powershell
   cd frontend
   .\start-frontend.bat
   ```

3. **Open Browser**
   http://localhost:3000

4. **Test Connection**
   - Dashboard should load
   - Check browser console for errors
   - Verify API calls in Network tab

## Troubleshooting Checklist

- [ ] Backend is running on port 5000
- [ ] Frontend starts without errors
- [ ] Browser opens at localhost:3000
- [ ] No CORS errors in console
- [ ] API calls succeed in Network tab
- [ ] Dashboard loads watchlist data

## Need Help?

- See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- Check [API_TESTING.md](../API_TESTING.md)
- Review browser console errors
- Check backend logs
