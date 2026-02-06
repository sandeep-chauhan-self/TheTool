# Frontend Architecture

## Overview

TheTool's frontend is a modern **React 18** single-page application (SPA) that provides a professional trading analysis interface. It communicates with the Flask backend via RESTful APIs and displays real-time stock analysis results.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend - React SPA"
        subgraph "Pages"
            Dashboard["Dashboard.js"]
            Results["Results.js"]
            AllStocks["AllStocksAnalysis.js"]
            Strategies["StrategiesIndex.js"]
        end

        subgraph "Components"
            Header["Header"]
            NavBar["NavigationBar"]
            Modals["Modals"]
            Cards["StockCards"]
        end

        subgraph "State Management"
            Context["StocksContext"]
            Cache["TTL Cache"]
        end

        subgraph "API Layer"
            ApiJs["api.js"]
            Axios["Axios Instance"]
        end
    end

    Dashboard --> Context
    Results --> Context
    AllStocks --> Context
    Context --> Cache
    Context --> ApiJs
    ApiJs --> Axios
    Axios -->|"HTTP/REST"| Backend["Flask Backend"]

    style Context fill:#e1f5fe
    style ApiJs fill:#fff3e0
    style Backend fill:#e8f5e9
```

---

## Technology Stack

| Technology     | Version | Purpose                                          |
| -------------- | ------- | ------------------------------------------------ |
| React          | 18.2    | Core UI framework (functional components, hooks) |
| React Router   | 6.20    | Client-side routing and navigation               |
| Axios          | 1.6.2   | HTTP client for API communication                |
| Tailwind CSS   | 3.3.5   | Utility-first CSS framework for styling          |
| PostCSS        | 8.4.32  | CSS processing and Tailwind compilation          |
| React Markdown | 9.1.0   | Rendering markdown content (strategy help pages) |

---

## Directory Structure

```text
frontend/
├── public/                     # Static assets
├── src/
│   ├── api/
│   │   └── api.js              # Centralized API client
│   │
│   ├── components/             # Reusable UI components
│   │   ├── AddStockModal.js
│   │   ├── AddToWatchlistModal.js
│   │   ├── AnalysisConfigModal.js
│   │   ├── BacktestResults.js
│   │   ├── Breadcrumbs.js
│   │   ├── Header.js
│   │   └── NavigationBar.js
│   │
│   ├── context/
│   │   └── StocksContext.js    # Global state management
│   │
│   ├── pages/                  # Page components (routed views)
│   │   ├── Dashboard.js
│   │   ├── AnalysisConfig.js
│   │   ├── Results.js
│   │   ├── AllStocksAnalysis.js
│   │   ├── StrategiesIndex.js
│   │   └── StrategyHelp.js
│   │
│   ├── utils/
│   │   └── tradingViewUtils.js
│   │
│   ├── App.js                  # Root component with routing
│   ├── index.js                # Application entry point
│   └── index.css               # Global styles
│
├── package.json
├── tailwind.config.js
└── Dockerfile
```

---

## Component Architecture

### Routing Structure

```mermaid
graph LR
    subgraph "React Router"
        Root["/"] --> Dashboard
        Config["/config"] --> AnalysisConfig
        ResultsRoute["/results/:ticker"] --> Results
        AllStocksRoute["/all-stocks"] --> AllStocksAnalysis
        StrategiesRoute["/strategies"] --> StrategiesIndex
        StrategyDetail["/strategies/:id"] --> StrategyHelp
        Backtest["/backtest"] --> BacktestResults
    end

    style Dashboard fill:#c8e6c9
    style Results fill:#c8e6c9
    style AllStocksAnalysis fill:#c8e6c9
```

### State Management Pattern

```mermaid
graph TB
    subgraph "StocksProvider"
        State["State
        • allStocks[]
        • watchlist[]
        • analysisResults{}
        • cacheTimestamps"]

        Functions["Functions
        • fetchAllStocks()
        • fetchWatchlistData()
        • updateStockAnalysis()
        • refreshAll()"]
    end

    subgraph "Consumer Components"
        Dashboard["Dashboard"]
        Results["Results"]
        AllStocks["AllStocksAnalysis"]
    end

    State --> Dashboard
    State --> Results
    State --> AllStocks
    Functions --> Dashboard
    Functions --> Results
    Functions --> AllStocks

    style State fill:#e3f2fd
    style Functions fill:#fff8e1
```

### Component Types

1. **Page Components** (`/pages/`)
   - Full-page views tied to routes
   - Handle data fetching and page-level state
   - Examples: `Dashboard.js`, `Results.js`

2. **UI Components** (`/components/`)
   - Reusable, presentation-focused
   - Receive data via props
   - Examples: `NavigationBar.js`, `AddStockModal.js`

3. **Context Providers** (`/context/`)
   - Manage global application state
   - Provide data caching and utilities
   - Example: `StocksContext.js`

---

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant API as api.js
    participant Backend as Flask API
    participant DB as PostgreSQL

    User->>Dashboard: Click "Analyze"
    Dashboard->>API: analyzeStocks(tickers)
    API->>Backend: POST /api/analysis/analyze
    Backend->>Backend: Create job_id
    Backend->>DB: INSERT analysis_jobs
    Backend-->>API: {job_id, status: "queued"}
    API-->>Dashboard: job_id

    loop Every 2 seconds
        Dashboard->>API: getJobStatus(job_id)
        API->>Backend: GET /api/analysis/status/{job_id}
        Backend->>DB: SELECT progress
        Backend-->>API: {status, progress}
        API-->>Dashboard: Update progress bar
    end

    Note over Backend: Background thread completes
    Backend->>DB: INSERT analysis_results

    Dashboard->>API: getJobStatus(job_id)
    API->>Backend: GET /api/analysis/status/{job_id}
    Backend-->>API: {status: "completed", results}
    API-->>Dashboard: Display results
    Dashboard->>User: Show analysis cards
```

---

## API Layer Architecture

The frontend uses a centralized API module (`src/api/api.js`):

### Environment Detection

```mermaid
flowchart TD
    Start["getApiBaseUrl()"] --> CheckEnv{REACT_APP_API_BASE_URL set?}
    CheckEnv -->|Yes| UseEnv["Use env variable"]
    CheckEnv -->|No| CheckHost{Check hostname}

    CheckHost -->|localhost| Local["http://localhost:5000"]
    CheckHost -->|the-tool-git-development*| Dev["Railway Dev URL"]
    CheckHost -->|the-tool-theta*| Prod["Railway Prod URL"]
    CheckHost -->|Other| Default["Default to localhost:5000"]

    style Local fill:#e8f5e9
    style Dev fill:#fff3e0
    style Prod fill:#ffebee
```

### API Functions

| Category  | Functions                                                              |
| --------- | ---------------------------------------------------------------------- |
| Analysis  | `analyzeStocks()`, `getJobStatus()`, `getReport()`, `downloadReport()` |
| Watchlist | `getWatchlist()`, `addToWatchlist()`, `removeFromWatchlist()`          |
| Stocks    | `getAllNSEStocks()`, `getStockHistory()`                               |
| Strategy  | `getStrategies()`, `getStrategy()`, `getStrategyHelp()`                |

---

## Caching Strategy

```mermaid
flowchart TD
    Request["Data Request"] --> CheckCache{Cache Valid?}
    CheckCache -->|"Yes (< 5 min)"| ReturnCache["Return Cached Data"]
    CheckCache -->|"No (expired/missing)"| FetchAPI["Fetch from API"]
    FetchAPI --> UpdateCache["Update Cache + Timestamp"]
    UpdateCache --> ReturnData["Return Fresh Data"]

    subgraph "Cache Structure"
        AllStocks["allStocks[]"]
        Watchlist["watchlist[]"]
        Results["analysisResults{}"]
        Timestamps["lastFetch timestamps"]
    end

    style ReturnCache fill:#c8e6c9
    style FetchAPI fill:#fff3e0
```

**TTL Configuration:**

```javascript
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const isCacheValid = (lastFetch) => {
  if (!lastFetch) return false;
  return Date.now() - lastFetch < CACHE_TTL;
};
```

---

## Key Design Patterns

### 1. Container/Presenter Pattern

Pages act as containers (data fetching) while components are presenters (rendering).

### 2. Polling for Real-time Updates

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Polling: Start Analysis
    Polling --> Polling: status = "processing"
    Polling --> Completed: status = "completed"
    Polling --> Failed: status = "failed"
    Completed --> Idle: Show Results
    Failed --> Idle: Show Error
```

### 3. Optimistic UI Updates

After adding/removing from watchlist, the UI updates immediately without waiting for server confirmation.

### 4. Environment-Based Configuration

API URLs are auto-detected based on hostname, eliminating the need for environment-specific builds.

---

## Styling Approach

The frontend uses **Tailwind CSS** for styling:

```javascript
// Utility Classes Example
<button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Analyze
</button>

// Responsive Design
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on tablet, third on desktop */}
</div>
```

---

## Build & Development

```bash
# Development server (hot reload)
npm run start

# Production build
npm run build

# Run tests
npm run test
```

---

## Integration Points

```mermaid
graph LR
    Frontend["React Frontend"]

    Frontend -->|"Axios HTTP"| Backend["Flask Backend API"]
    Frontend -->|"External Links"| TradingView["TradingView Charts"]
    Frontend -->|".env files"| EnvConfig["Environment Config"]
    Frontend -->|"Nginx static"| Docker["Docker Deployment"]

    style Frontend fill:#e3f2fd
    style Backend fill:#e8f5e9
```
