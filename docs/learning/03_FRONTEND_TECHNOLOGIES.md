# Technologies and Concepts Used in Frontend

## Overview

This document explains all technologies, libraries, concepts, and patterns used in TheTool's frontend application.

---

## Core Technologies

### 1. React 18.2

**What it is:** A JavaScript library for building user interfaces using a component-based architecture.

**Key Concepts Used:**

#### a) Functional Components

All components use function syntax instead of class syntax:

```javascript
function Dashboard() {
  const [watchlist, setWatchlist] = useState([]);
  return <div>{/* JSX content */}</div>;
}
```

#### b) Hooks

React's way to add state and lifecycle features to functional components:

| Hook          | Purpose                                 | Example Usage                                          |
| ------------- | --------------------------------------- | ------------------------------------------------------ |
| `useState`    | Manage component state                  | `const [loading, setLoading] = useState(false)`        |
| `useEffect`   | Side effects (API calls, subscriptions) | `useEffect(() => { fetchData() }, [])`                 |
| `useCallback` | Memoize functions                       | `const handleClick = useCallback(() => {...}, [deps])` |
| `useMemo`     | Memoize expensive calculations          | `const sorted = useMemo(() => data.sort(), [data])`    |
| `useContext`  | Consume context values                  | `const { watchlist } = useContext(StocksContext)`      |
| `useNavigate` | Programmatic navigation                 | `const navigate = useNavigate()`                       |
| `useParams`   | Access URL parameters                   | `const { ticker } = useParams()`                       |

#### c) JSX (JavaScript XML)

Syntax extension that allows writing HTML-like code in JavaScript:

```jsx
return (
  <div className="container">
    <button onClick={handleClick}>
      {isLoading ? "Loading..." : "Analyze"}
    </button>
  </div>
);
```

#### d) Conditional Rendering

```jsx
{
  isLoading && <Spinner />;
}
{
  error ? <ErrorMessage error={error} /> : <Results data={data} />;
}
```

#### e) List Rendering

```jsx
{
  stocks.map((stock) => <StockRow key={stock.ticker} stock={stock} />);
}
```

---

### 2. React Router DOM 6.20

**What it is:** Standard routing library for React applications.

**Key Concepts:**

#### a) BrowserRouter

Wraps the entire app to enable routing:

```jsx
<BrowserRouter>
  <App />
</BrowserRouter>
```

#### b) Routes and Route

Define which component renders for which URL:

```jsx
<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/results/:ticker" element={<Results />} />
</Routes>
```

#### c) Dynamic Routes

URL parameters for dynamic pages:

```jsx
<Route path="/results/:ticker" element={<Results />} />;

// Accessing the parameter
const { ticker } = useParams(); // ticker = "RELIANCE.NS"
```

#### d) Navigation

```jsx
// Using Link component
<Link to="/config">Configure</Link>;

// Programmatic navigation
const navigate = useNavigate();
navigate("/results/AAPL");
```

---

### 3. Context API (State Management)

**What it is:** React's built-in solution for sharing state across components without prop drilling.

**Why used instead of Redux:**

- Simpler setup
- No external dependencies
- Sufficient for medium-sized applications
- Built into React

**Implementation Pattern:**

```jsx
// 1. Create context
const StocksContext = createContext(null);

// 2. Create provider
export function StocksProvider({ children }) {
  const [allStocks, setAllStocks] = useState([]);

  const value = {
    allStocks,
    fetchAllStocks: async () => {
      /* ... */
    },
  };

  return (
    <StocksContext.Provider value={value}>{children}</StocksContext.Provider>
  );
}

// 3. Create custom hook
export function useStocks() {
  const context = useContext(StocksContext);
  if (!context) {
    throw new Error("useStocks must be used within StocksProvider");
  }
  return context;
}

// 4. Usage in components
function Dashboard() {
  const { allStocks, fetchAllStocks } = useStocks();
  // ...
}
```

---

### 4. Axios 1.6.2

**What it is:** Promise-based HTTP client for making API requests.

**Why used instead of native fetch:**

- Automatic JSON transformation
- Request/response interceptors
- Request timeout support
- Browser compatibility
- Cleaner syntax

**Key Features Used:**

#### a) Creating an Instance

```javascript
const api = axios.create({
  baseURL: "http://localhost:5000",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": process.env.REACT_APP_API_KEY,
  },
});
```

#### b) HTTP Methods

```javascript
// GET request
const response = await api.get("/api/watchlist");

// POST request
const response = await api.post("/api/analysis/analyze", { tickers, capital });

// DELETE request with body
const response = await api.delete("/api/watchlist", { data: { ticker } });
```

#### c) Response Handling

```javascript
export const analyzeStocks = async (tickers, config) => {
  const response = await api.post("/api/analysis/analyze", payload);
  return response.data; // Axios auto-parses JSON
};
```

---

### 5. Tailwind CSS 3.3.5

**What it is:** Utility-first CSS framework for rapid UI development.

**Core Concepts:**

#### a) Utility Classes

Style directly in JSX without writing CSS:

```jsx
<button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Analyze
</button>
```

#### b) Responsive Design

Mobile-first breakpoints:

```jsx
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on tablet, third on desktop */}
</div>
```

#### c) State Variants

```jsx
<button className="bg-blue-500 hover:bg-blue-700 focus:ring-2 disabled:opacity-50">
```

#### d) Color System

```
text-gray-100     // Very light (text)
bg-gray-800       // Dark (backgrounds)
border-blue-500   // Primary color
text-green-600    // Success
text-red-600      // Error
```

#### e) Flexbox & Grid

```jsx
<div className="flex items-center justify-between gap-4">
<div className="grid grid-cols-3 gap-4">
```

#### f) Spacing Scale

```
// Margin
m-4     // 1rem (16px)
mx-auto // Horizontal auto-center
mt-8    // Top margin 2rem

// Padding
p-4     // 1rem
px-6    // Horizontal 1.5rem
py-2    // Vertical 0.5rem
```

---

### 6. PostCSS 8.4.32

**What it is:** A tool for transforming CSS with JavaScript plugins.

**Used for:**

- Processing Tailwind CSS
- Autoprefixing for browser compatibility
- CSS minification in production

**Configuration:**

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

---

### 7. React Markdown 9.1.0

**What it is:** Component for rendering Markdown as React elements.

**Used for:**

- Rendering strategy help/documentation pages
- Displaying formatted content from backend

**Usage:**

```jsx
import ReactMarkdown from "react-markdown";

function StrategyHelp({ content }) {
  return (
    <div className="prose">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
```

---

## JavaScript Concepts Used

### 1. Async/Await

Modern syntax for handling Promises:

```javascript
const fetchData = async () => {
  try {
    const response = await api.get("/api/stocks");
    setStocks(response.data);
  } catch (error) {
    setError(error.message);
  }
};
```

### 2. Destructuring

Extracting values from objects/arrays:

```javascript
// Object destructuring
const { ticker, name, score } = stock;

// Array destructuring
const [loading, setLoading] = useState(false);

// Props destructuring
function StockRow({ stock, onSelect, onRemove }) {
  // ...
}
```

### 3. Spread Operator

```javascript
// Copying and extending objects
const newStock = { ...stock, analyzed: true };

// Combining arrays
const allStocks = [...existingStocks, ...newStocks];
```

### 4. Template Literals

String interpolation:

```javascript
const url = `/api/analysis/status/${jobId}`;
const message = `Analyzing ${count} stocks`;
```

### 5. Array Methods

| Method      | Purpose            | Example                                       |
| ----------- | ------------------ | --------------------------------------------- |
| `map()`     | Transform array    | `stocks.map(s => s.ticker)`                   |
| `filter()`  | Filter array       | `stocks.filter(s => s.score > 50)`            |
| `find()`    | Find single item   | `stocks.find(s => s.ticker === 'AAPL')`       |
| `some()`    | Check if any match | `stocks.some(s => s.hasError)`                |
| `reduce()`  | Accumulate values  | `stocks.reduce((sum, s) => sum + s.score, 0)` |
| `forEach()` | Iterate            | `stocks.forEach(s => console.log(s))`         |

### 6. Optional Chaining

Safe property access:

```javascript
const name = response?.data?.stock?.name || "Unknown";
```

### 7. Nullish Coalescing

Default values for null/undefined:

```javascript
const capital = config.capital ?? 100000; // Only uses 100000 if null/undefined
```

---

## Design Patterns

### 1. Container/Presenter Pattern

- **Container components** (pages): Handle data fetching, state management
- **Presenter components**: Receive props, render UI

### 2. Custom Hooks Pattern

Extracting reusable logic:

```javascript
function usePolling(callback, interval) {
  useEffect(() => {
    const id = setInterval(callback, interval);
    return () => clearInterval(id);
  }, [callback, interval]);
}
```

### 3. Provider Pattern

Wrapping app with context providers:

```jsx
<StocksProvider>
  <Router>
    <App />
  </Router>
</StocksProvider>
```

### 4. Compound Components

Related components that work together:

```jsx
<Modal>
  <Modal.Header>Title</Modal.Header>
  <Modal.Body>Content</Modal.Body>
  <Modal.Footer>Actions</Modal.Footer>
</Modal>
```

---

## Development Tooling

### 1. Create React App (react-scripts 5.0.1)

- Development server with hot reload
- Production build optimization
- Webpack configuration abstraction
- ESLint integration

### 2. ESLint

JavaScript linting for code quality:

```json
{
  "eslintConfig": {
    "extends": ["react-app"]
  }
}
```

### 3. Environment Variables

```javascript
// Access in code
process.env.REACT_APP_API_URL;
process.env.REACT_APP_DEBUG;

// Must be prefixed with REACT_APP_
```

---

## Performance Concepts

### 1. Memoization

Preventing unnecessary re-renders:

```javascript
const sortedStocks = useMemo(() => {
  return [...stocks].sort((a, b) => b.score - a.score);
}, [stocks]); // Only recalculate when stocks change
```

### 2. Callback Memoization

```javascript
const handleClick = useCallback(() => {
  analyzeStock(ticker);
}, [ticker]); // Stable reference unless ticker changes
```

### 3. Client-Side Caching

TTL-based caching in StocksContext:

```javascript
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const isCacheValid = (lastFetch) => {
  return Date.now() - lastFetch < CACHE_TTL;
};
```

### 4. Lazy Loading (Potential)

Code splitting for large components:

```javascript
const AllStocksAnalysis = React.lazy(() => import("./pages/AllStocksAnalysis"));
```

---

## Browser APIs Used

### 1. localStorage/sessionStorage

Persisting data between sessions:

```javascript
localStorage.setItem("lastTicker", ticker);
const lastTicker = localStorage.getItem("lastTicker");
```

### 2. setInterval/setTimeout

Polling for job status:

```javascript
const intervalId = setInterval(() => {
  checkJobStatus(jobId);
}, 2000);

// Cleanup
clearInterval(intervalId);
```

### 3. Blob API

For file downloads:

```javascript
const blob = new Blob([response.data]);
const url = window.URL.createObjectURL(blob);
```

---

## Key Libraries Summary

| Library          | Version | Purpose              |
| ---------------- | ------- | -------------------- |
| react            | 18.2.0  | Core UI framework    |
| react-dom        | 18.2.0  | React DOM bindings   |
| react-router-dom | 6.20.0  | Client-side routing  |
| axios            | 1.6.2   | HTTP client          |
| react-markdown   | 9.1.0   | Markdown rendering   |
| tailwindcss      | 3.3.5   | Utility-first CSS    |
| autoprefixer     | 10.4.16 | CSS vendor prefixing |
| postcss          | 8.4.32  | CSS processing       |
