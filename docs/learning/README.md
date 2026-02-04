# TheTool - Learning Documentation

This folder contains comprehensive documentation about the TheTool project architecture, technologies, and implementation details. It's designed to help developers understand the project and prepare for technical interviews.

---

## 📚 Documentation Index

| #   | Document                                                                 | Description                                                                         |
| --- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| 01  | [Frontend Architecture](./01_FRONTEND_ARCHITECTURE.md)                   | React component structure, routing, state management, and styling approach          |
| 02  | [Backend Architecture](./02_BACKEND_ARCHITECTURE.md)                     | Flask application structure, blueprints, indicators, strategies, and database layer |
| 03  | [Frontend Technologies](./03_FRONTEND_TECHNOLOGIES.md)                   | Deep dive into React, React Router, Axios, Tailwind CSS, and Context API            |
| 04  | [Backend Technologies](./04_BACKEND_TECHNOLOGIES.md)                     | Deep dive into Flask, pandas, yfinance, PostgreSQL, and threading                   |
| 05  | [Frontend-Backend Connection](./05_FRONTEND_BACKEND_CONNECTION.md)       | API communication, CORS, data transformation, error handling                        |
| 06  | [Lifecycle: Frontend → Database](./06_LIFECYCLE_FRONTEND_TO_DATABASE.md) | Complete data write flow with code snippets                                         |
| 07  | [Lifecycle: Database → Frontend](./07_LIFECYCLE_DATABASE_TO_FRONTEND.md) | Complete data read flow with code snippets                                          |
| 08  | [Libraries and Processes](./08_LIBRARIES_AND_PROCESSES.md)               | Detailed explanations of all major libraries and design patterns                    |
| 09  | [Interview Questions](./09_INTERVIEW_QUESTIONS.md)                       | 120+ interview questions covering all project aspects                               |

---

## 🎯 How to Use This Documentation

### For Learning

1. Start with **01_FRONTEND_ARCHITECTURE** and **02_BACKEND_ARCHITECTURE** for high-level understanding
2. Read **03** and **04** for technology deep-dives
3. Study **06** and **07** for data flow understanding
4. Review **08** for library and pattern explanations

### For Interview Preparation

1. Read through **09_INTERVIEW_QUESTIONS**
2. Practice explaining concepts from architecture docs
3. Be able to trace data flow from frontend to database and back
4. Understand the design patterns used

### For Contributing

1. Understand the project structure from architecture docs
2. Follow the patterns documented in **08_LIBRARIES_AND_PROCESSES**
3. Ensure your code fits within the established conventions

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Pages     │  │ Components  │  │   Context   │                 │
│  │ (Dashboard, │  │ (Modals,    │  │ (Stocks     │                 │
│  │  Results)   │  │  Cards)     │  │  Provider)  │                 │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘                 │
│         │                                  │                        │
│         └────────────────┬─────────────────┘                        │
│                          ▼                                          │
│                   ┌─────────────┐                                   │
│                   │   API Layer │ (axios)                           │
│                   └──────┬──────┘                                   │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Flask)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Routes    │  │  Orchestrator│ │  Indicators │                 │
│  │ (Blueprints)│──│ (Analysis   │──│ (RSI, MACD, │                 │
│  │             │  │  Pipeline)   │ │  etc.)      │                 │
│  └──────┬──────┘  └─────────────┘  └─────────────┘                 │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐  ┌─────────────┐                                  │
│  │  Database   │  │   Thread    │                                  │
│  │  (query_db) │  │   Tasks     │                                  │
│  └──────┬──────┘  └─────────────┘                                  │
└─────────┼───────────────────────────────────────────────────────────┘
          │ SQL/psycopg2
          ▼
    ┌─────────────┐
    │ PostgreSQL  │
    │  Database   │
    └─────────────┘
```

---

## 📊 Technology Stack Summary

### Frontend

| Technology     | Purpose             |
| -------------- | ------------------- |
| React 18       | UI framework        |
| React Router 6 | Client-side routing |
| Axios          | HTTP client         |
| Tailwind CSS   | Styling             |
| Context API    | State management    |

### Backend

| Technology | Purpose              |
| ---------- | -------------------- |
| Flask 3.0  | Web framework        |
| pandas     | Data manipulation    |
| yfinance   | Stock data           |
| ta         | Technical indicators |
| psycopg2   | PostgreSQL driver    |
| threading  | Background jobs      |

### Database

| Technology   | Purpose           |
| ------------ | ----------------- |
| PostgreSQL   | Data persistence  |
| JSON columns | Indicator storage |

---

## 🔄 Key Data Flows

### Analysis Flow

```
User clicks "Analyze"
  → POST /api/analysis/analyze
  → Create job_id
  → Start background thread
  → Fetch OHLCV (yfinance)
  → Calculate 12 indicators
  → Aggregate score
  → Save to database
  → Poll status until complete
  → Display results
```

### Read Flow

```
User navigates to /results/:ticker
  → GET /api/analysis/report/:ticker
  → Query database
  → Parse JSON fields
  → Return formatted response
  → Render UI components
```

---

## 📝 Quick Reference

### File Locations

| What            | Where                                    |
| --------------- | ---------------------------------------- |
| Frontend entry  | `frontend/src/index.js`                  |
| Routes          | `frontend/src/App.js`                    |
| API functions   | `frontend/src/api/api.js`                |
| Global state    | `frontend/src/context/StocksContext.js`  |
| Backend entry   | `backend/app.py`                         |
| Analysis logic  | `backend/utils/analysis_orchestrator.py` |
| Indicators      | `backend/indicators/*.py`                |
| Database        | `backend/database.py`                    |
| Background jobs | `backend/infrastructure/thread_tasks.py` |

### Main API Endpoints

| Endpoint                       | Method          | Purpose              |
| ------------------------------ | --------------- | -------------------- |
| `/api/analysis/analyze`        | POST            | Start analysis       |
| `/api/analysis/status/:id`     | GET             | Check job status     |
| `/api/analysis/report/:ticker` | GET             | Get analysis results |
| `/api/watchlist`               | GET/POST/DELETE | Manage watchlist     |
| `/api/stocks/nse`              | GET             | Get NSE stocks list  |
| `/api/strategies`              | GET             | List strategies      |

---

## 📖 Further Reading

- [React Documentation](https://react.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [Technical Analysis Library (ta)](https://technical-analysis-library-in-python.readthedocs.io/)
