# Category Intelligence Implementation Plan
**Target Release**: Q1 2025 | **Risk Level**: LOW | **Breaking Changes**: NONE

---

## Executive Summary

Implement a **6-phase layered approach** to add category-aware intelligence to signal aggregation without breaking existing functionality. Phases 0-1 are **zero-risk** foundational work. Subsequent phases are gated by configuration flags.

---

## Phase 0: Snapshot Tests (Foundation - Safety Lock)

### Objective
Create baseline tests to prove that all changes preserve existing behavior.

### Requirements

#### R0.1: Snapshot Test Infrastructure
- **File**: `backend/test_signal_snapshots.py`
- **Purpose**: Golden copy of current outputs for regression detection
- **Scope**: 
  - 10 real stocks with varying characteristics
  - 3 time periods (bullish, bearish, neutral market)
  - Store full response JSON

#### R0.2: Test Data Collection
- **Stocks to snapshot**:
  ```
  BULLISH_REGIME:
  - RELIANCE.NS (large cap, trending)
  - INFY.NS (tech, momentum)
  
  BEARISH_REGIME:
  - SBIN.NS (declining)
  - TATASTEEL.NS (downtrend)
  
  NEUTRAL_REGIME:
  - HDFCBANK.NS (consolidation)
  - TCS.NS (sideways)
  - WIPRO.NS (low volatility)
  
  EXTREME:
  - AARTIDRUGS.NS (high volatility)
  - 63MOONS.NS (illiquid)
  - RELIANCE (historical crash data)
  ```

#### R0.3: Snapshot Artifacts
- **Store**: `backend/tests/snapshots/signal_snapshots.json`
- **Format**:
  ```json
  {
    "RELIANCE.NS": {
      "date": "2025-12-21",
      "market_regime": "bullish",
      "snapshot": {
        "score": 0.75,
        "verdict": "Buy",
        "confidence": 0.82,
        "total_indicators": 12,
        "indicators": [...],
        "strategy_used": 5
      }
    }
  }
  ```

#### R0.4: Regression Test Suite
- **Test Functions**:
  - `test_score_unchanged()` - Score must be exact match (±0.01 tolerance)
  - `test_verdict_unchanged()` - Verdict must be identical
  - `test_confidence_unchanged()` - Confidence within ±2%
  - `test_indicator_order()` - Same indicators returned
  - `test_no_new_fields()` - No unexpected JSON fields

- **Acceptance Criteria**:
  - All 10 stocks pass all 5 tests
  - Snapshots committed to git
  - CI pipeline enforces snapshot comparison

#### R0.5: Snapshot Update Process
- **File**: `backend/scripts/update_snapshots.py`
- **Process**:
  1. Run analysis on all 10 stocks
  2. Generate new snapshots
  3. Display diff for manual review
  4. Require explicit approval before commit
- **Safety**: Old snapshots backed up in `snapshots/backup/`

---

## Phase 1: Add Category Metadata (Structure - Zero Logic Change)

### Objective
Organize indicators into categories with metadata, enabling Phase 2 analysis without affecting current behavior.

### Requirements

#### R1.1: Indicator Metadata Registry
- **File**: `backend/utils/analysis/indicator_metadata.py`
- **Purpose**: Single source of truth for indicator-category mappings
- **Content**:

```python
INDICATOR_METADATA = {
    # Momentum Indicators
    "RSI": {
        "category": "momentum",
        "description": "Relative Strength Index",
        "period": 14,
        "datasource": "legacy"
    },
    "MACD": {
        "category": "trend",
        "description": "Moving Average Convergence Divergence",
        "datasource": "legacy"
    },
    "Stochastic": {
        "category": "momentum",
        "description": "Stochastic Oscillator",
        "datasource": "legacy"
    },
    "CCI": {
        "category": "momentum",
        "description": "Commodity Channel Index",
        "datasource": "legacy"
    },
    "Williams %R": {
        "category": "momentum",
        "description": "Williams Percent Range",
        "datasource": "legacy"
    },
    
    # Trend Indicators
    "ADX": {
        "category": "trend",
        "description": "Average Directional Index",
        "datasource": "legacy"
    },
    "Parabolic SAR": {
        "category": "trend",
        "description": "Stop and Reverse",
        "datasource": "legacy"
    },
    "EMA Crossover": {
        "category": "trend",
        "description": "Exponential Moving Average",
        "datasource": "legacy"
    },
    
    # Volatility Indicators
    "ATR": {
        "category": "volatility",
        "description": "Average True Range",
        "datasource": "legacy"
    },
    "Bollinger Bands": {
        "category": "volatility",
        "description": "Bollinger Bands",
        "datasource": "legacy"
    },
    
    # Volume Indicators
    "OBV": {
        "category": "volume",
        "description": "On-Balance Volume",
        "datasource": "legacy"
    },
    "Chaikin Money Flow": {
        "category": "volume",
        "description": "CMF",
        "datasource": "legacy"
    },
}

CATEGORIES = {
    "momentum": {
        "indicators": 5,
        "weight": 0.8,
        "description": "Price momentum and oscillators"
    },
    "trend": {
        "indicators": 4,
        "weight": 1.3,
        "description": "Directional trend confirmation"
    },
    "volatility": {
        "indicators": 2,
        "weight": 1.2,
        "description": "Volatility and risk measures"
    },
    "volume": {
        "indicators": 2,
        "weight": 1.5,
        "description": "Volume and money flow"
    }
}
```

#### R1.2: Category Grouping Helper
- **File**: `backend/utils/analysis/category_grouper.py`
- **Function**: `group_indicators_by_category(indicator_results: List[Dict]) -> Dict`

**Signature**:
```python
def group_indicators_by_category(indicator_results):
    """
    Group indicator results by their category.
    
    Args:
        indicator_results: List of dicts with 'name', 'vote', 'confidence', etc.
        
    Returns:
        {
            "momentum": [
                {"name": "RSI", "vote": 1, "confidence": 0.8, ...},
                {"name": "Stochastic", "vote": 1, "confidence": 0.7, ...}
            ],
            "trend": [...],
            "volatility": [...],
            "volume": [...]
        }
    """
```

**Implementation**:
- Uses `INDICATOR_METADATA` to classify
- Handles missing metadata gracefully (defaults to "unknown")
- Returns ordered dict with consistent key order
- Zero transformation of data (read-only grouping)

#### R1.3: Category Summary Calculator
- **File**: `backend/utils/analysis/category_grouper.py`
- **Function**: `calculate_category_summary(grouped_indicators: Dict) -> Dict`

**Returns**:
```python
{
    "momentum": {
        "count": 5,
        "votes": [1, 1, 0, -1, 1],
        "confidences": [0.8, 0.7, 0.0, 0.6, 0.9],
        "average_vote": 0.4,
        "average_confidence": 0.6
    },
    "trend": { ... },
    "volatility": { ... },
    "volume": { ... }
}
```

**Formulas**:
- `average_vote = sum(votes) / len(votes)`
- `average_confidence = sum(confidences) / len(confidences)`

#### R1.4: Integration Point (Non-Breaking)
- **File**: `backend/utils/analysis_orchestrator.py`
- **Location**: After `aggregate_votes()` completes
- **Code**:
```python
# Existing code continues unchanged
score = SignalAggregator.aggregate_votes(indicator_results, ...)
verdict = SignalAggregator.get_verdict(score)

# NEW: Add metadata (does not affect score/verdict)
grouped = group_indicators_by_category(indicator_results)
category_summary = calculate_category_summary(grouped)

# Return enhanced result (backward compatible)
result = {
    "score": score,
    "verdict": verdict,
    "confidence": confidence,
    # ... all existing fields ...
    
    # NEW fields (optional, safe to ignore)
    "_phase1_metadata": {
        "grouped_indicators": grouped,
        "category_summary": category_summary
    }
}
```

#### R1.5: Unit Tests for Phase 1
- **File**: `backend/tests/test_category_metadata.py`
- **Test Cases**:

| Test | Requirement |
|------|-------------|
| `test_all_indicators_mapped()` | Every indicator has metadata |
| `test_metadata_complete()` | Each entry has all required fields |
| `test_category_weights_valid()` | All weights >= 0 |
| `test_grouper_preserves_data()` | No data loss when grouping |
| `test_grouper_handles_unknown()` | Unknown indicators don't crash |
| `test_summary_math_correct()` | Averages calculated correctly |
| `test_api_response_unchanged()` | Existing API response format preserved |

#### R1.6: Configuration Registry
- **File**: `backend/config.py`
- **New Entries**:
```python
# Phase 0-1: Safe foundational work
SNAPSHOT_TESTS_ENABLED = os.getenv('SNAPSHOT_TESTS_ENABLED', 'false').lower() == 'true'
PHASE1_METADATA_ENABLED = os.getenv('PHASE1_METADATA_ENABLED', 'true').lower() == 'true'

# Phases 2-6 will add more flags
PHASE2_CATEGORY_ANALYZER_ENABLED = os.getenv('PHASE2_CATEGORY_ANALYZER_ENABLED', 'false').lower() == 'true'
CATEGORY_INTELLIGENCE_MODE = os.getenv('CATEGORY_INTELLIGENCE_MODE', 'OFF')  # OFF | ADVISORY | ENFORCED
```

---

## Acceptance Criteria (Phase 0 + 1)

### Must-Have (Blocking)
- ✅ All snapshot tests pass
- ✅ Zero breaking changes to API response
- ✅ All unit tests for Phase 1 pass (100% code coverage for new files)
- ✅ Backward compatibility verified (old clients work unchanged)
- ✅ Configuration flags working

### Should-Have (Nice-to-Have)
- ✅ Documentation updated
- ✅ README includes metadata structure
- ✅ Example response with metadata shown

### Won't-Have (Future Phases)
- ❌ Category-based logic changes (Phase 2+)
- ❌ Confidence boosts (Phase 4+)
- ❌ Volatility gates (Phase 5+)

---

## Deliverables (Phase 0 + 1)

### Code Files
```
backend/utils/analysis/
├── indicator_metadata.py          (NEW)
└── category_grouper.py            (NEW)

backend/tests/
├── test_signal_snapshots.py       (NEW)
└── test_category_metadata.py      (NEW)

backend/tests/snapshots/
├── signal_snapshots.json          (NEW)
└── backup/                        (NEW, empty initially)

backend/scripts/
└── update_snapshots.py            (NEW)

backend/config.py                  (MODIFIED - add flags)
backend/utils/analysis_orchestrator.py (MODIFIED - non-breaking)
```

### Documentation Files
```
CATEGORY_INTELLIGENCE_PHASES_01.md     (NEW - this file's continuation)
CATEGORY_INTELLIGENCE_ROADMAP.md       (NEW - Phases 2-6 planning)
```

### Test Artifacts
```
backend/tests/snapshots/signal_snapshots.json    (10 stocks, 3 regimes)
backend/tests/snapshots/backup/                  (version history)
```

---

## Timeline & Effort Estimate

### Phase 0: Snapshot Tests
- **Effort**: 4-6 hours
  - Setup test infrastructure: 1 hour
  - Collect real data: 2 hours
  - Write snapshot tests: 1-2 hours
  - Document process: 1 hour

### Phase 1: Metadata + Grouping
- **Effort**: 3-4 hours
  - Create metadata registry: 1 hour
  - Implement grouper: 1 hour
  - Write unit tests: 1 hour
  - Integration & docs: 1 hour

### Total: ~7-10 hours (1-2 days)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Snapshot test flaky | LOW | MEDIUM | Run 3x, log market state |
| Regression in Phase 1 | LOW | LOW | Unit test coverage 100% |
| Performance impact | VERY LOW | MEDIUM | Profile memory usage |
| API breaks | VERY LOW | HIGH | Backward compat tests |

---

## Success Metrics

- ✅ Phase 0: All 10 stocks' snapshots stored, tests pass
- ✅ Phase 1: All 12 indicators mapped, grouper 100% accurate
- ✅ Both: Zero breaking changes (verify with integration tests)
- ✅ Both: Ready for Phase 2 (metadata enables CategoryAnalyzer)

---

## Next Steps (After Phase 0-1 Complete)

1. **Phase 2**: CategoryAnalyzer (read-only analysis)
2. **Phase 3**: Shadow evaluation (internal logging)
3. **Phase 4**: Soft influence (confidence adjustments)
4. **Phase 5**: Controlled overrides (rule gates)
5. **Phase 6**: Config-driven modes

---

## Approval & Sign-Off

- [ ] Requirements reviewed
- [ ] Timeline acceptable
- [ ] Risk mitigation approved
- [ ] Ready to implement Phase 0
- [ ] Ready to implement Phase 1
