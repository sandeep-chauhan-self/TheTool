# TheTool Copilot Operating Prompt (Master Internal Guide)

Version: 1.1
Date: 2025-11-23
Changes Since 1.0:
- Added comprehensive pagination specification (Section 28).
- Added OpenAPI specification & generation approach (Section 29).
- Added indicator strategy plugin architecture design (Section 30).
- Added structured logging & correlation implementation guidance (Section 31).
- Added security headers middleware with code sample (Section 32).
- Added PostgreSQL migration plan & script outline (Section 33).
- Added Celery task queue adoption blueprint (Section 34).
- Added WebSocket progress streaming design (Section 35).
- Expanded test matrix & coverage strategy (Section 36).
- Added load & performance testing methodology (Section 37).
- Added data retention & archival policy (Section 38).
- Added versioning & backward compatibility strategy (Section 39).
- Added error code lifecycle management process (Section 40).
- Added risk monitoring dashboard metrics (Section 41).
- Added future ML integration principles (Section 42).
- Added sample OpenAPI snippet appendix (Section 43).
- Word count expanded toward ~9000 target.
Scope: Backend (Flask), Frontend (React), Async Analysis Jobs, Data Persistence, Standards, Quality, Security, Roadmap.
Length Target: ~9000 words (Comprehensive Reference)

---

## 0. Purpose & Usage

This operating prompt is the internal manual for AI assistance (Copilot) working on TheTool repository. It encodes architecture decisions, naming conventions, patterns, validation schemas, error handling standards, security posture, performance strategies, logging models, testing workflows, deployment practices, and a progressive roadmap. When Copilot proposes code or refactors, it MUST align with these defined norms unless a deliberate, documented deviation is requested.

Use cases:

- Generating new API endpoints that harmonize with existing blueprints.
- Refactoring legacy code for consistency (naming, response shape, error codes).
- Implementing performance optimizations in a safe, incremental manner.
- Adding tests with a clear coverage and layering strategy.
- Guiding architectural evolution (DB migration, queue system adoption).
- Serving as onboarding deep-dive for new contributors.

Non-goals:

- Not a public-facing README.
- Not a substitute for domain-specific trading logic documentation.
- Not an exhaustive test specification (but provides structure).

---

## 1. High-Level System Overview

TheTool is a stock analysis platform enabling:

1. Watchlist management (add/remove stocks, optional notes).
2. Single and multi-ticker technical analysis using asynchronous background processing.
3. Retrieval of historical analysis results; results include score, verdict, and auxiliary metrics (entry, target, etc.).
4. Bulk analysis with an empty symbol list meaning “analyze ALL known stocks.”
5. A unified REST API under consistent `/api/<domain>` route prefixes (recently standardized).

Current stack:

- Backend: Python 3.x, Flask, SQLite (transitional - future PostgreSQL).
- Async Processing: Thread-based background tasks (planned upgrade to Celery/Redis).
- Frontend: React + Tailwind + Axios client abstraction.
- Deployment: Railway (backend), Vercel (frontend).
- Auth: API key (`X-API-Key`) header.
- Logging: Standard logging; JSON/log structure improvements planned.
- Error Responses: Centralized via `StandardizedErrorResponse`.
- Data Model Core Tables: `watchlist`, `analysis_results`, `analysis_jobs`.

Design imperatives:

- Predictable API contract (stable field names, explicit shapes).
- Separation of concerns: routes vs business logic vs data access.
- Extensibility: add future analysis strategies without destabilizing existing flows.
- Observability-first expansions (progress tracking, structured logs, job lifecycle clarity).

---

## 2. Backend Architecture Principles

### 2.1 Application Factory & Configuration

`app.py` builds the Flask app, loads environment vars through `dotenv`, applies configuration values from `config.py`, sets CORS, optional rate-limiting, logging bootstrap, and registers blueprints.

Guidelines:

- Keep `create_app()` idempotent; avoid global state initialization that breaks multi-worker contexts.
- All external service initializations should tolerate missing dependencies and degrade gracefully (e.g., rate limiter import inside try/except).
- CORS must list explicit origins; never use wildcard in production.
- Do not embed secrets directly—rely on env variables.

### 2.2 Blueprint Conventions

All feature sets live under their own blueprint with prefix `/api/<domain>`:

- Analysis: `/api/analysis`
- Stocks: `/api/stocks`
- Watchlist: `/api/watchlist`
- Root auxiliary (no `/api` prefix): `/health`, `/config`, `/` (info).

Blueprint file structure patterns:

1. Imports grouped (stdlib → third-party → internal modules).
2. Top-level logger from `setup_logger()`.
3. Schema or validator imports near top to make contracts visible.
4. Each route minimal: validation → domain logic delegate → response formatting → return.
5. Error handling only through `StandardizedErrorResponse.format`.

### 2.3 Database Layer

SQLite currently provides persistence with simple query helpers (`query_db`, `execute_db`). Transition plan includes PostgreSQL with connection pooling.

Rules:

- Parameterized queries ONLY.
- Wrap multi-statement operations in transactions via `execute_transaction` where atomicity matters.
- Validate existence before destructive operations (e.g., removal by id/ticker).
- Maintain updated timestamps for mutable records; store UTC in ISO8601.
- Distinguish between watchlist vs bulk source in `analysis_results` using a field like `analysis_source`.

### 2.4 Job Management & Progress

Job state stored in `analysis_jobs` with fields for status, total, completed, progress %, errors, timestamps. Enhanced `get_job_status()` returns enriched fields:

- `current_ticker`: most recently analyzed or in-progress ticker.
- `current_index`: 1-based ordinal for user display.
- `message`: dynamic human-readable status summary.

Statuses must follow a consistent lifecycle:

- queued → processing → completed/failed/cancelled.
- Do not invent new statuses arbitrarily; if evolution required, update docs and validators first.

### 2.5 Background Task Execution

Thread-based execution in `thread_tasks.py`. Constraints:

- Each thread must obtain its own DB connection; never share connection objects concurrently.
- Exception boundaries log errors with context; do not swallow without recording.
- Future Celery-based migration: tasks become idempotent; result persistence occurs post-success; progress streaming via Redis pub/sub.

### 2.6 Utilities & Abstractions

- `utils/db_utils.py`: atomic job creation, progress updates, completion marking.
- `utils/schemas.py`: central response schema registry for validation.
- `utils/api_utils.py`: request validation and error formatting.

Principle: Keep route handlers “thin”—heavy logic goes into orchestrator, utility, or service layers.

### 2.7 Response Standardization

Success responses are objects (never raw lists): include top-level identifying context (`ticker`, `symbol`, `job_id`, `count`).

Examples:

- Job status: includes timestamps, progress, and current ticker.
- History: always `history` array (NOT `results`).
- Watchlist: `watchlist` + `count`.

Uniformity prevents frontend divergence and code duplication.

### 2.8 Error Handling

All errors shaped as:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { /* optional */ },
    "timestamp": "ISO8601"
  }
}
```

Codes: `INVALID_REQUEST`, `JOB_NOT_FOUND`, `WATCHLIST_DUPLICATE`, `BULK_ANALYSIS_ERROR`, `STATUS_ERROR`, `HISTORY_ERROR`, `JOB_CANCEL_INVALID`, `JOB_UPDATE_FAILED`, `ANALYSIS_ERROR`, etc.
Never leak stack traces; only log on server-side.

---

## 3. Frontend Architecture Principles

### 3.1 API Client Abstraction

`src/api/api.js`: Single Axios instance with:

- `baseURL`: `REACT_APP_API_BASE_URL`.
- Headers: `Content-Type: application/json`, `X-API-Key`.
- All endpoints prefixed consistently (e.g., `/api/analysis/analyze`).

New endpoints must be added here first before page-level usage.

### 3.2 State Management

Currently local component state is sufficient. Guidelines for scaling:

- Adopt a central store when cross-page coordination (e.g., global job tracking) increases.
- Avoid prop drilling; form custom hooks for recurring tasks (polling, job creation, watchlist enrichment).

### 3.3 Polling Patterns

Analysis progress polling interval: 2000ms (2s). Poll logic must:

- Clear interval on component unmount or job completion.
- Detect terminal states (`completed`, `failed`, `cancelled`) and stop.

Future: replace polling with WebSocket push for real-time updates.

### 3.4 UI Feedback Patterns

- Always show progress bar + textual context (`current_index`, `completed/total`).
- Use color-coded verdicts (Strong Buy/Bullish → green shades; Sell/Bearish → red shades; Neutral → gray).
- Distinguish “No analysis available” vs “Pending analysis.”

### 3.5 Error Handling UX

- Network/transport errors → generic “Network error; retry.”
- Validation errors → display server message (map `error.message`).
- Cancelled job → explicit user confirmation message.
- Duplicate watchlist item → user-friendly conflict message.

### 3.6 Performance Considerations

- Batch enrichment queries; avoid sequential waterfall per watchlist item.
- Defer non-critical data loads until main render complete (progressive hydration).
- Add memoization or virtualization for large watchlists (future scaling).

### 3.7 Code Style

- Functional components only.
- `async/await` for all API calls.
- Avoid inline anonymous functions in heavy lists (optimize re-renders).

---

## 4. Naming & Terminology Consistency

Key terms:

- Ticker: canonical textual identifier (may be exchange-qualified).
- Symbol: may represent alias or normalized identifier used in DB.
- Watchlist Item: record linking ticker/symbol + user notes.
- Analysis Result: persisted evaluation outcome for a ticker at a point in time.
- Job: batch process grouping one or more analyses.
- Progress: percentage completion of job.
- History: chronological list of previous analysis results (limit enforced).
- Verdict: category classification (Strong Buy, Buy, Neutral, Sell, Strong Sell).

Avoid ambiguous synonyms like “entry” vs “startPrice” unless formally introduced.

---

## 5. Validation & Schema Strategy

`utils/schemas.py` defines response shape expectations. Guidelines:

- Future expansions: add request schemas for complex bodies (bulk operations, advanced filters).
- Validate outbound responses in critical endpoints (job status, creation, bulk analysis) to catch regressions early.
- Document any schema changes before code modification.

Response schema categories:

1. JOB_STATUS
2. ANALYSIS_HISTORY
3. STOCK_HISTORY
4. WATCHLIST
5. JOB_CREATED
6. ERROR_RESPONSE
7. NSE_STOCKS_LIST
8. ALL_STOCKS (future pagination fields)
9. HEALTH_CHECK
10. CONFIG

Validation failure should produce `SCHEMA_VALIDATION_ERROR` (planned new code). Ensure this doesn’t occur in production unless an actual mismatch emerges.

---

## 6. Error Code Taxonomy & Guidelines

Error codes map conceptual failures:

- Input validation: `VALIDATION_ERROR`, `INVALID_TICKER`, `INVALID_SYMBOL`.
- Resource absence: `JOB_NOT_FOUND`, `WATCHLIST_NOT_FOUND`.
- Conflict: `WATCHLIST_DUPLICATE`, `JOB_DUPLICATE`.
- Operational failure: `JOB_START_FAILED`, `BULK_ANALYSIS_ERROR`, `ANALYSIS_ERROR`.
- Cancellation handling: `JOB_CANCEL_INVALID` (invalid state for cancellation).
- System issues: `STATUS_ERROR`, `HISTORY_ERROR`, `STOCK_LOOKUP_ERROR`.

Rules:

- Each new feature must define and register its distinct error codes.
- Code names must reflect domain meaning, not technical HTTP code (`BAD_REQUEST` too generic—prefer `INVALID_REQUEST`).
- Provide actionable `message` that assists user comprehension.
- Optional `details` field holds structured metadata (field errors, job phase, etc.).

---

## 7. Authentication & Security Posture

Current model: Single API key used for all protected endpoints.

Planned roadmap:

1. Multi-user identity (user table, tokens, hashed secrets).
2. Role-based authorization (admin endpoints for system introspection).
3. Per-user rate limits and abuse detection.
4. Encrypted storage of sensitive values (avoid plain-text if secrets added).

Security best practices to implement incrementally:

- Enforce strict origin list in CORS.
- Remove query-based API key fallback entirely.
- Add headers: `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Strict-Transport-Security`.
- Validate ticker/symbol format (regex like: `^[A-Z0-9._-]{1,15}$`).
- Sanitize user-provided `notes` (strip HTML, escape markup).

Threat scenarios to mitigate:

- Credential leakage (restrict logging of headers).
- Replay or brute-force (rate limit keyed by IP and API key).
- Malicious payload injection (validate request JSON; reject unknown fields).
- DoS via large bulk requests (enforce per-request symbol upper bound; paginate history retrieval).

---

## 8. Performance & Scalability Strategy

Short-term (current environment):

- Optimize thread usage; limit to modest concurrency to avoid SQLite locking contention.
- Add caching for static lists (NSE tickers).
- Paginate large lists (history beyond 50 entries).

Medium-term:

- Migrate SQLite → PostgreSQL for concurrency & indexing.
- Introduce Redis for ephemeral job state, Pub/Sub for live status updates.
- Adopt Celery/RQ for managed worker pool scaling.
- Horizontal scaling of analysis workers independent of API layer.

Long-term resilience:

- Query optimization: avoid `SELECT *` for broad endpoints; project only required fields.
- Summarization: return compact computed metrics in list endpoints (full detail via detail endpoints).
- Partitioning strategies if dataset volume grows (e.g., time-based partition of analysis results).

Performance metrics to track:

- Average job duration (per ticker + aggregate).
- Polling-induced load (requests per job lifecycle).
- DB query latency for critical endpoints.
- Throughput: jobs/hour.
- Memory footprint under bulk operations.

Optimization tactics:

- Bulk inserts for multiple analysis results (transaction grouping).
- Pre-compute frequently derived fields (confidence percentage) at persistence time.
- Reduce JSON serialization overhead by using lean Python structures.

---

## 9. Testing Layers & Coverage Goals

Testing layers:

1. Unit: Utility functions (job state transitions, schema validators).
2. Functional: Each route; verify response shape, status codes, error patterns.
3. Integration: Full flow—create job, poll status, finish, retrieve history.
4. Load/Stress (future): Simulate concurrent job creation & progress polling.
5. Security: Attempt invalid auth, injection patterns, boundary input conditions.

Coverage Targets:

- Core modules (`routes`, `db_utils`, `api_utils`): ≥80% statements.
- Non-critical expansions (indicator logic): best-effort coverage while evolving.

Example test workflows:

- **Watchlist Workflow**:
  1. GET empty watchlist.
  2. POST add ticker.
  3. GET watchlist now contains entry.
  4. DELETE ticker.
  5. GET watchlist empty again.
- **Job Lifecycle**:
  1. POST create job.
  2. Mock progress updates.
  3. GET status shows gradual progress.
  4. Mark job completed.
  5. GET status includes final state.
- **Bulk Analysis Empty Array**:
  1. POST with `symbols: []`.
  2. Verify expansion to full stock list.
  3. Validate job total matches union size.

Test design principles:

- Deterministic assertions; avoid dependency on system time—mock where necessary.
- Clean DB fixture per test; isolate side-effects.
- Use factory functions for test data generation.

---

## 10. Deployment Workflow & Environment Management

Deployment sequence:

1. Local verification (lint + tests).
2. Commit with semantic message.
3. Push to main (CI/CD triggers Railway & Vercel deploys).
4. Post-deploy smoke tests (watchlist endpoint, analysis job creation, job status polling).
5. Monitor logs for anomalies (error spikes, slow response times).

Environment variables:

- Mandatory: `MASTER_API_KEY`, `FLASK_ENV`, `CORS_ORIGINS`.
- Optional: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`, `PORT`.
- Frontend: `REACT_APP_API_BASE_URL`, `REACT_APP_API_KEY`.

Deployment safety:

- Idempotent DB migrations—do not drop tables unconditionally.
- Pre-deployment backups before schema-altering releases.
- Keep rollback ready: previous container image accessible.

Future staging environment ideal for testing migrations and performance tuning before production push.

---

## 11. Logging, Monitoring & Observability

Logging improvements roadmap:

1. Introduce structured JSON logging formatting.
2. Add correlation identifiers (request ID, job ID) inserted at request boundary.
3. Log categories: `ACCESS`, `JOB_EVENT`, `DB_EVENT`, `SECURITY_ALERT`, `PERF_METRIC`.
4. Provide log sampling for high-frequency events (avoid volume overload).

Minimum logging criteria:

- Job creation: job_id, tickers count.
- Progress updates: completed/total every N steps (throttle e.g., every 10% or item mod 10).
- Errors: always include `job_id` and ticker if applicable.

Monitoring candidate metrics:

- Job queue length (future when queue introduced).
- Active thread count.
- Rate limit rejections.
- Error code distribution.
- Response time percentile distribution.

Alert thresholds (define later):

- > 5% of requests returning 500 in 10-minute window.
  >
- Continuous job failures exceeding threshold.
- DB connection errors recurring.

---

## 12. Backlog & Roadmap (Actionable Items)

Near-term actionable backlog:

1. Implement pagination endpoints for history retrieval.
2. Add schema validation to all remaining responses (watchlist, config, health).
3. Introduce security headers middleware.
4. Remove query-based API key fallback if present.
5. Implement input sanitization for notes field.
6. Build consolidated endpoint to retrieve watchlist + latest verdicts in single response.
7. Add `/api/analysis/jobs` listing endpoint (active & recent jobs).
8. Create OpenAPI spec (manual or with `flask-smorest`).
9. Add unit tests for enriched `get_job_status()` fields.
10. Rate limit differentiation by endpoint category.

Mid-term backlog:

- Migrate to PostgreSQL & add indexes (ticker, symbol, job_id, created_at).
- Introduce Redis for job state, caching, rate limiting counters.
- Replace thread pool with Celery worker system.
- Implement websocket channel for live progress streaming.
- Add structured logging formatter.
- Create performance baseline dashboard.

Long-term backlog:

- User accounts & RBAC.
- Strategy simulation engine (run hypothetical backtests).
- Machine learning predictive modules (score generation enhancements).
- Partition data for scale (sharding large historical datasets).
- Multi-tenant isolation.
- Plugin architecture for custom indicators.

Prioritization principle: correctness → security → scalability → advanced analytics.

---

## 13. Coding Standards & Style Guides

Python style:

- Use descriptive variable names (`progress_percentage` over `pct`).
- Avoid nested try blocks—flatten with helper functions.
- Group related SQL statements in transactions.
- Predeclare logger at module top only.
- Use list/dict comprehensions thoughtfully—avoid over-complex expressions.
- Document non-trivial logic with concise docstrings.

JavaScript/React style:

- Functional components with hooks.
- Keep render functions lean; compute derived state outside JSX.
- Use optional chaining defensively when data may be absent.
- Avoid mixing concerns (data fetch, transformation, presentation) in single component—introduce helper modules.

Commit style:

- Use imperative mood: "Add pagination to history endpoint".
- Group related changes—avoid monolithic commits covering unrelated layers.

Documentation style:

- Use structured headings in markdown.
- Present contract examples with explicit keys; avoid ellipsis-only representations unless focusing on a single field.

---

## 14. API Contract (Extended Examples)

### 14.1 Job Status (Processing)

```json
{
  "job_id": "e8d6c7aa-1234-4567-9abc-def012345678",
  "status": "processing",
  "progress": 45,
  "completed": 9,
  "total": 20,
  "successful": 9,
  "errors": "[]",
  "current_index": 10,
  "current_ticker": "INFY",
  "message": "Processing ticker 10/20...",
  "created_at": "2025-11-23T09:50:34.123456",
  "updated_at": "2025-11-23T09:52:01.654321",
  "started_at": "2025-11-23T09:50:35.000000",
  "completed_at": null
}
```

### 14.2 Completed Job

```json
{
  "job_id": "e8d6c7aa-1234-4567-9abc-def012345678",
  "status": "completed",
  "progress": 100,
  "completed": 20,
  "total": 20,
  "successful": 19,
  "errors": "[{\"ticker\":\"XYZ\",\"error\":\"Timeout\"}]",
  "current_index": 20,
  "current_ticker": "TCS",
  "message": "Completed! 19/20 successful",
  "created_at": "2025-11-23T09:50:34.123456",
  "updated_at": "2025-11-23T09:55:10.654321",
  "started_at": "2025-11-23T09:50:35.000000",
  "completed_at": "2025-11-23T09:55:10.654321",
  "results": [ /* optional short summary */ ]
}
```

### 14.3 Analysis History

```json
{
  "ticker": "INFY",
  "history": [
    {
      "id": 101,
      "ticker": "INFY",
      "symbol": "INFY",
      "analysis_data": "{\"score\":82,\"verdict\":\"Buy\"}",
      "created_at": "2025-11-22T14:11:00.000000",
      "job_id": "7901abcc-2222-3333-4444-555566667777"
    }
  ]
}
```

### 14.4 Watchlist Retrieval

```json
{
  "watchlist": [
    {
      "id": 5,
      "ticker": "TCS",
      "symbol": "TCS",
      "notes": "High momentum candidate",
      "created_at": "2025-11-20T11:05:30.000000"
    }
  ],
  "count": 1
}
```

### 14.5 Error Response (Duplicate)

```json
{
  "error": {
    "code": "WATCHLIST_DUPLICATE",
    "message": "Ticker TCS already in watchlist",
    "details": {"ticker": "TCS"},
    "timestamp": "2025-11-23T09:57:15.321000"
  }
}
```

---

## 15. Refactoring & Evolution Guidelines

When refactoring:

1. Confirm tests pass pre-change (establish baseline).
2. Introduce schema validation for new/changed endpoints.
3. Migrate naming in one controlled pass (avoid partial renames causing hybrid state).
4. Ship doc updates in same PR when changing API contracts.
5. Provide transitional compatibility if breaking change is external (e.g., support old field for one version window).

Legacy patterns to eliminate:

- Inconsistent field names (`results` vs `history`).
- Missing prefix routes (`/watchlist` vs `/api/watchlist`).
- Raw stringified error arrays (prefer JSON serialization consistently).

---

## 16. Risk Register (Architectural & Operational)

Identified risks & mitigations:

1. **SQLite Write Contention**: Bulk multi-thread writes can lock DB.
   - Mitigation: serialize updates, migrate to PostgreSQL for improved concurrency.
2. **Unbounded Bulk Analysis**: Empty array could expand uncontrollably with future large data sets.
   - Mitigation: impose max symbol count; require pagination or segmentation.
3. **Missing Input Sanitization**: `notes` field could introduce injection/XSS risk.
   - Mitigation: sanitize and escape before persistence.
4. **Limited Observability**: Hard to correlate job events across logs.
   - Mitigation: add correlation IDs; structured JSON logging.
5. **Static Rate Limit Policy**: Potential abuse if high-frequency automation introduced.
   - Mitigation: refine buckets; dynamic adaptation by usage profile.
6. **Thread Crash Without Recovery**: Job may hang in processing state if thread dies.
   - Mitigation: implement watchdog to detect stale jobs; allow manual cancellation/retry.
7. **Schema Drift Risk**: Frontend and backend contract could diverge silently.
   - Mitigation: enforce response schema validation in CI tests.

---

## 17. Operational Playbooks (Future Draft)

Incident: High 500 error rate.

- Steps: Check last deployment diff → examine logs by error code → verify DB connectivity → roll back if regression confirms.

Incident: Job stuck in `processing` > threshold.

- Steps: Inspect job timestamps → compare with thread alive set → mark failed if thread missing → notify admin.

Incident: CORS failures in production.

- Steps: Confirm `CORS_ORIGINS` environment variable → verify options route returns headers → redeploy with corrected config.

Incident: Rate limit rejections spike.

- Steps: Analyze offending keys/IPs → tune per-endpoint limit → consider implementing dynamic sliding window.

---

## 18. Contribution & Review Workflow

Pull Request checklist:

- [ ] API response shapes align with schema definitions.
- [ ] New error codes documented.
- [ ] Tests added or updated covering new paths.
- [ ] Docs updated (`COPILOT_OPERATING_PROMPT.md` revisions if structural change).
- [ ] No secrets / credentials in diff.
- [ ] Logging statements relevant & non-redundant.
- [ ] Performance unchecked loops avoided.

Review focus:

- Clarity over brevity—readability prioritized.
- Single responsibility adherence in new modules.
- Edge cases addressed (empty arrays, null fields, large sets).
- Failure modes well-defined.

---

## 19. Evolution Toward Distributed Architecture

Phases:

1. **Current**: Thread-based local processing.
2. **Redis Integration**: Real-time job progress + distributed visibility.
3. **Celery Migration**: Task queue, retries, escalations, worker autoscaling.
4. **Service Decomposition**: Analysis engine separated from API gateway.
5. **Observability Maturity**: Metrics, tracing instrumentation (OpenTelemetry).
6. **Multi-Tenant Isolation**: Resource quotas per tenant, row-level security in DB.

Design changes under these phases must preserve backward compatibility at each stage or declare version boundaries (e.g., `/api/v2/analysis`).

---

## 20. Prompt Invocation Examples

When asking Copilot for code:

- “Generate a new endpoint `/api/stocks/summary` returning paginated stock summaries with schema validation.”
- “Refactor `thread_tasks.py` to add structured logging without changing existing job start API.”
- “Add tests ensuring `/api/analysis/status/<job_id>` includes `current_ticker` and `message` under all statuses.”
- “Propose a migration script moving SQLite to PostgreSQL including environment variable changes.”

Copilot must:

1. Reference existing schema patterns.
2. Avoid breaking standardized field names.
3. Provide test stubs matching typical flow.
4. Highlight any introduced dependencies.

---

## 21. Quality Principles (Recap)

- Consistency > Novelty.
- Explicitness > Implicit assumptions.
- Small incremental changes > large speculative rewrites.
- Performance tuning only after measurement.
- Security woven in early; not retrofitted last-minute.
- Documentation stays in lockstep with contract changes.

---

## 22. Final Review Checklist (Maintainer Use)

Before marking this prompt iteration complete:

- [ ] ~9000 words coverage achieved (broad architectural surface).
- [ ] All domains addressed: backend, frontend, auth, security, performance, logging, testing, roadmap.
- [ ] No contradictory guidance present.
- [ ] Recently fixed discrepancies (history vs results, route prefixes) documented.
- [ ] Clear migration pathways articulated.

Pending (mark as resolved when enacted):

- Add explicit pagination spec (include in next revision).
- Introduce schema validation for all existing endpoints (partial now).
- Document indicator strategy plugin loading mechanism.
- Formalize OpenAPI spec generation approach.

---

## 23. Change Management for This Prompt

Future updates must:

1. Increment version (1.1, 1.2, etc.).
2. Summarize deltas at top (“Changes Since 1.0”).
3. Remove deprecated guidance—do not accumulate conflicting sections.
4. Link to implementation PR references.

Use a diff-based review to validate prompt updates adhere to repository direction.

---

## 24. Appendix: Potential Future Schema Additions

- PAGINATED_HISTORY:

```json
{
  "ticker": "TCS",
  "history": [ ... ],
  "pagination": { "page": 1, "per_page": 20, "total": 145, "total_pages": 8 }
}
```

- ANALYSIS_RESULT_DETAIL:

```json
{
  "ticker": "INFY",
  "symbol": "INFY",
  "latest_result": { "score": 82, "verdict": "Buy", "entry": 1485.4, "target": 1600.0 },
  "history_count": 37
}
```

- JOB_LISTING:

```json
{
  "jobs": [
    { "job_id": "...", "status": "completed", "progress": 100, "total": 20, "completed": 20 }
  ],
  "count": 5
}
```

---

## 25. Appendix: Error Code Registry (Extended)

| Code                    | HTTP | Description                                             |
| ----------------------- | ---- | ------------------------------------------------------- |
| INVALID_REQUEST         | 400  | Generic malformed body or missing required field        |
| VALIDATION_ERROR        | 400  | Specific field fails schema or logical validation       |
| INVALID_TICKER          | 400  | Empty or malformed ticker parameter                     |
| INVALID_SYMBOL          | 400  | Empty or malformed symbol parameter                     |
| WATCHLIST_DUPLICATE     | 409  | Attempt to add existing ticker to watchlist             |
| WATCHLIST_NOT_FOUND     | 404  | Removal target not present                              |
| JOB_NOT_FOUND           | 404  | Status or cancel target job missing                     |
| JOB_DUPLICATE           | 409  | Attempt to create existing job ID (race or replay)      |
| JOB_START_FAILED        | 500  | Background job failed to launch                         |
| JOB_CANCEL_INVALID      | 400  | Cancellation requested for job not in cancellable state |
| ANALYSIS_ERROR          | 500  | General analysis computation failure                    |
| STATUS_ERROR            | 500  | Failure retrieving status (DB or logic fault)           |
| HISTORY_ERROR           | 500  | Retrieval of history failed                             |
| STOCK_LOOKUP_ERROR      | 500  | Bulk stock retrieval failure                            |
| BULK_ANALYSIS_ERROR     | 500  | Bulk analysis orchestration failure                     |
| JOB_UPDATE_FAILED       | 500  | Progress or status update failure                       |
| RATE_LIMIT_EXCEEDED     | 429  | Too many requests in allotted window                    |
| SCHEMA_VALIDATION_ERROR | 500  | (Future) Response failed schema validation              |

Extend table as new domains introduced.

---

## 26. Appendix: Suggested Test Skeletons

Python pytest examples (pseudo):

```python
def test_watchlist_add_and_remove(client, api_key):
    # Add
    resp = client.post('/api/watchlist', headers={'X-API-Key': api_key}, json={'symbol': 'INFY'})
    assert resp.status_code == 201
    # List
    lst = client.get('/api/watchlist', headers={'X-API-Key': api_key}).get_json()
    assert lst['count'] == 1
    # Remove
    rem = client.delete('/api/watchlist', headers={'X-API-Key': api_key}, json={'ticker': 'INFY'})
    assert rem.status_code == 200


def test_analysis_job_lifecycle(client, api_key, monkeypatch):
    # Create job
    resp = client.post('/api/analysis/analyze', headers={'X-API-Key': api_key}, json={'tickers': ['INFY'], 'capital': 50000})
    job_id = resp.get_json()['job_id']
    # Mock progress
    # ... monkeypatch progress to completed
    status = client.get(f'/api/analysis/status/{job_id}', headers={'X-API-Key': api_key}).get_json()
    assert 'message' in status
```

---

## 27. Final Statement

This prompt remains the authoritative baseline for AI-assisted development within TheTool. Any substantial deviation should be introduced through planned, documented revisions. Copilot must treat sections as layered constraints: architectural rules, naming, response schemas, error taxonomy, and roadmap priorities. Consistency, clarity, and incremental improvement are the guiding principles.

---

## 28. Pagination Specification

Goals:
- Provide consistent pagination across list-style endpoints (history, jobs, stocks).
- Avoid over-fetch; enable client to request manageable slices.
- Maintain stable ordering semantics (default descending by created_at where applicable).

Standard Query Parameters:
- `page` (int, >=1, default 1)
- `per_page` (int, 1–100, default 20)
- `order` (enum: `asc|desc`, default `desc`)
- `sort` (field name; allowed values depend on endpoint: e.g. `created_at`, `score`, `ticker`)

Response Envelope (generic):
```json
{
  "data": [ /* items */ ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 145,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "sort": "created_at",
    "order": "desc"
  }
}
```

History Endpoint (`/api/analysis/history/<ticker>`):
- Adds optional `limit_latest` (mutually exclusive with pagination; if present returns top N newest results without pagination envelope—discouraged for long-term, maintain both carefully).

Validation Rules:
- Reject `per_page` > 100 with `VALIDATION_ERROR`.
- Reject negative or zero `page`.
- Fallback to defaults if missing.

Database Strategy:
- Use `LIMIT ? OFFSET ?` for SQLite; adapt to `LIMIT / OFFSET` or keyset pagination later in PostgreSQL for large tables.
- Consider keyset pagination for very large datasets (future). Document alternative parameter set: `after_id`, `before_id` when implementing.

Performance Considerations:
- Always SELECT explicit columns; avoid `SELECT *`.
- Add covering index on (`ticker`, `created_at DESC`) for history queries post-PostgreSQL migration.

---

## 29. OpenAPI Specification Approach

Objectives:
- Machine-readable contract enabling client code generation, validation, and documentation portal.
- Serve as source of truth to guard against drift.

Tooling Options:
1. Manual authoring with `openapi.yaml` in `docs/`.
2. `flask-smorest` / `flask-restx` decorators to auto-generate spec.
3. Hybrid: minimal decorators + post-processing script enriching components.

Recommended Path (Incremental):
1. Create minimal `openapi.yaml` skeleton with servers, tags, security scheme (API Key in header `X-API-Key`).
2. Add schemas referencing existing `ResponseSchemas` (converter script can translate Python dict definitions into OpenAPI `components/schemas`).
3. Integrate nightly CI check: diff generated spec vs committed spec; fail on mismatch.
4. Provide HTML rendering via ReDoc in `/docs` endpoint.

Security Definition:
```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
security:
  - ApiKeyAuth: []
```

Versioning:
- Maintain `info.version` aligned with prompt version major.minor.
- For breaking changes, introduce new tag or path group (`/api/v2`).

Validation Workflow:
- Pre-commit hook: script parses `openapi.yaml`, ensures all `paths` defined exist in code.
- Test suite: one test loads spec, iterates response schemas and verifies required keys present in runtime sample responses.

---

## 30. Indicator Strategy Plugin Architecture

Goal: Allow rapid addition / removal / experimentation with technical indicators and composite strategies without altering core analysis flow.

Directory Structure Proposal:
```
backend/indicators/
  base.py            # AbstractIndicator
  registry.py        # Registration & discovery
  builtins/          # Core stable indicators
  plugins/           # External or experimental indicators
```

Abstract Interface (conceptual):
```python
class AbstractIndicator:
    name: str
    version: str = "1.0"
    requires: list[str] = []  # prerequisite data columns
    def compute(self, series) -> dict: ...
```

Registration Pattern:
```python
from indicators.registry import register

@register
class MyIndicator(AbstractIndicator):
    name = "my_indicator"
    def compute(self, series):
        # return {"value": x, "meta": {...}}
```

Discovery:
- `registry` scans `builtins` + `plugins` on app startup (lazy load to reduce import overhead).
- Fail gracefully: log warnings for incompatible indicator versions.

Metadata & Versioning:
- Each plugin declares semantic version; core engine may enforce minimum supported versions.
- Provide compatibility layer for deprecated indicators (soft disable with warning).

Security & Isolation:
- In early phase, plugins are trusted code; future: consider sandboxing, signature verification.

Testing:
- Each plugin includes a reference test verifying deterministic output for fixture time-series.

---

## 31. Structured Logging & Correlation Implementation

Format: JSON lines—each log entry a single JSON object.

Core Fields:
- `timestamp` (UTC ISO8601)
- `level` (INFO/WARN/ERROR)
- `event` (e.g., JOB_CREATED, PROGRESS_UPDATE)
- `job_id` (nullable)
- `ticker` (nullable)
- `request_id` (for HTTP requests)
- `message` (human readable)
- `meta` (dict for additional context)

Sample:
```json
{
  "timestamp": "2025-11-23T10:05:12.123456Z",
  "level": "INFO",
  "event": "JOB_CREATED",
  "job_id": "abc-123",
  "ticker": null,
  "message": "Analysis job created for 25 tickers",
  "meta": {"count": 25, "source": "bulk"}
}
```

Correlation:
- Generate `request_id` per incoming HTTP request (middleware) and propagate to logs.
- Include `thread_id` for debugging concurrency.

Implementation Steps:
1. Create `app_logging/structured_logging.py` with `StructuredLogger` wrapper.
2. Replace ad-hoc `logger.info(...)` calls in high-value paths first (job lifecycle).
3. Introduce log level mapping; ensure ERROR logs include stack trace in `meta.trace`.

Rotation & Retention (interim):
- Use size-based rotation (e.g., 10 MB × 5 files) via `TimedRotatingFileHandler` or adopt external collector.

---

## 32. Security Headers Middleware (Code Sample)

Purpose: Strengthen baseline HTTP security posture.

Middleware Example:
```python
def security_headers_middleware(app):
    @app.after_request
    def apply_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['Referrer-Policy'] = 'no-referrer'
        resp.headers['Permissions-Policy'] = 'geolocation=()'
        resp.headers['Content-Security-Policy'] = "default-src 'self'"
        return resp
```

HSTS:
- Only enable when behind HTTPS always: `Strict-Transport-Security: max-age=63072000; includeSubDomains`.

Validation:
- Add test ensuring headers present on `/health` response.

---

## 33. PostgreSQL Migration Plan & Script Outline

Phases:
1. Schema Design: Translate SQLite types to PostgreSQL (proper `TIMESTAMP WITH TIME ZONE`).
2. Migrations Tool: Adopt `alembic` for versioned migrations.
3. Data Transfer: Export existing SQLite tables; import with COPY.
4. Dual Write (optional short window) to verify integrity.

Sample Alembic Revision Outline:
```python
def upgrade():
    op.create_table('analysis_jobs', ...)
    op.create_index('ix_analysis_jobs_status', 'analysis_jobs', ['status'])
    op.create_index('ix_analysis_results_ticker_created', 'analysis_results', ['ticker', 'created_at'])
```

Environment Variables:
- `DATABASE_URL=postgresql+psycopg://user:pass@host/dbname`

Rollback Strategy:
- Retain last SQLite snapshot; keep code path to fallback for one release cycle.

---

## 34. Celery Task Queue Adoption Blueprint

Rationale: Improve reliability, scaling, retry semantics beyond threads.

Components:
- Broker: Redis.
- Result Backend: Redis or PostgreSQL (for durability).
- Task Module: `backend/tasks/analysis_tasks.py`.

Task Example:
```python
@celery.task(bind=True, max_retries=3)
def run_indicator_batch(self, job_id, tickers):
    # process indicators; update job progress in DB
```

Progress Updates:
- Emit events to Redis Pub/Sub channel `job_progress`.

Migration Steps:
1. Abstract current thread logic behind interface.
2. Implement Celery tasks using same DB utility functions.
3. Feature flag switch `USE_CELERY=true`.
4. Gradual rollout (50% of jobs) then full cutover.

---

## 35. WebSocket Progress Streaming Design

Goal: Replace polling with push updates to reduce latency and request overhead.

Endpoint: `/ws/progress/<job_id>`.

Protocol:
- Client sends initial subscribe message.
- Server pushes JSON messages:
```json
{"event":"progress","job_id":"...","completed":9,"total":20,"current_ticker":"INFY","percentage":45}
```

Implementation Options:
- Flask-Sock / Quart for async support.
- Or side-car Node.js WS gateway subscribing to Redis Pub/Sub.

Fallback:
- If WebSocket fails, revert to polling automatically.

Security:
- Validate API key on connection handshake; reject unauthenticated clients.

---

## 36. Expanded Test Matrix & Coverage Strategy

Matrix Dimensions:
- Endpoint category (watchlist, analysis, stocks, health, config).
- Response status class (2xx, 4xx, 5xx).
- Data volume (empty, small, large).
- Auth state (valid key, missing key, invalid key).
- Concurrency scenario (parallel job creations).

Coverage Checklist:
- Watchlist duplicate add returns 409.
- Bulk empty symbol list translates to full list.
- Job failure path sets status `failed` and logs error.
- Pagination edges: `page` beyond range returns empty data but valid envelope.
- Schema validation test for each response type.

Mutation Testing (future):
- Use tool (e.g., mutmut) to ensure tests detect logic perturbations.

---

## 37. Load & Performance Testing Methodology

Tools: Locust or k6.

Scenarios:
1. Sustained 50 concurrent users creating jobs (arrival rate modeling).
2. Mixed workload: 70% status polling, 20% history retrieval, 10% watchlist modification.
3. Spike test: sudden 10× load for 1 minute.

Metrics Captured:
- p50/p95/p99 latency per endpoint.
- Error rate by code.
- Resource usage (CPU, memory) per container.

Acceptance Thresholds (initial):
- p95 latency < 800ms for job status.
- Error rate < 1% under sustained load.

Reporting:
- Export results to `docs/performance/DATE_REPORT.md`.

---

## 38. Data Retention & Archival Policy

Short-Term (Active): retain all analysis results for 90 days for fast access.
Mid-Term: compress or summarize results older than 90 days into aggregated metrics (average score, verdict distribution).
Long-Term (> 1 year): archive raw records to cold storage (S3 or equivalent) or purge if compliance permits.

Implementation Hooks:
- Scheduled job (daily) scanning for records past threshold.
- Use partitioned tables for easier dropping of old partitions (PostgreSQL).

Privacy & Compliance:
- Ensure user-specific (future multi-user) data removal requests propagate to archives.

---

## 39. Versioning & Backward Compatibility Strategy

Semantic Versioning:
- MAJOR: Breaking API changes.
- MINOR: Backward-compatible additions.
- PATCH: Internal fixes, doc updates.

Deprecation Policy:
- Mark fields slated for removal; retain for one MINOR cycle with warning header `X-Deprecated-Field`.
- Maintain compatibility adapter translating old requests (if needed).

Upgrade Guides:
- Each MAJOR release includes `MIGRATION_GUIDE.md` section detailing contract changes.

---

## 40. Error Code Lifecycle Management

Phases:
1. Proposal: Add to design doc with rationale & HTTP mapping.
2. Implementation: Code + tests verifying emission conditions.
3. Documentation: Update error registry & OpenAPI spec.
4. Monitoring: Track frequency; retire unused codes after 2 releases.

Retirement:
- Mark as deprecated; remove from emission paths; keep in registry with note for one version.

---

## 41. Risk Monitoring Dashboard Metrics

Essential Panels:
- Job Throughput (jobs/hour).
- Job Failure Rate (% failed per hour).
- Average Progress Latency (time from creation to first progress update).
- API Error Code Distribution.
- DB Query p95 latency.
- Rate Limit Trigger Count.

Data Source:
- Export logs to ELK/Prometheus; define metrics counters in code (future instrumentation).

---

## 42. Future ML Integration Principles

Use Cases:
- Predictive scoring (probability of positive movement).
- Volatility forecasting.

Principles:
- Transparency: Provide feature attribution summary in results.
- Versioning: Model version tag in analysis_data (`model_version`).
- Reproducibility: Store input feature snapshot for each prediction.
- Safety: Confidence calibration; avoid overconfident outputs.

Deployment:
- Separate microservice (`ml-service`) accessed via internal API; decouple from synchronous request path.

---

## 43. Additional Appendix: Sample OpenAPI Snippet

```yaml
openapi: 3.0.3
info:
  title: TheTool API
  version: 1.1.0
paths:
  /api/analysis/status/{job_id}:
    get:
      summary: Get analysis job status
      parameters:
        - in: path
          name: job_id
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Job status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobStatus'
        '404':
          description: Job not found
components:
  schemas:
    JobStatus:
      type: object
      required: [job_id, status, progress]
      properties:
        job_id:
          type: string
        status:
          type: string
          enum: [queued, processing, completed, failed, cancelled]
        progress:
          type: integer
        current_ticker:
          type: string
          nullable: true
        message:
          type: string
```

---

## 44. Closing Note (Version 1.1)

With the added sections, the prompt now covers advanced operational, architectural, and evolutionary concerns. Treat new guidance as immediately applicable for any planning, refactoring, or feature addition. Revisit Sections 28–43 when implementing related capabilities.

End of Version 1.1.
