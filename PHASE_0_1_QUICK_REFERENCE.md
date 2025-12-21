# Phase 0-1 Quick Reference: Implementation Checklist

## Phase 0: Snapshot Tests

### Step 0.1: Create Test Infrastructure
```bash
File: backend/test_signal_snapshots.py

Tasks:
□ Import pytest, json, datetime
□ Create @pytest.fixture for 10 test stocks
□ Create fixture for snapshot storage path
□ Implement load_snapshot(ticker) function
□ Implement save_snapshot(ticker, data) function
```

### Step 0.2: Collect Snapshots
```bash
File: backend/tests/snapshots/signal_snapshots.json

Stocks to snapshot:
□ RELIANCE.NS   (bullish_regime)
□ INFY.NS       (bullish_regime)
□ SBIN.NS       (bearish_regime)
□ TATASTEEL.NS  (bearish_regime)
□ HDFCBANK.NS   (neutral_regime)
□ TCS.NS        (neutral_regime)
□ WIPRO.NS      (neutral_regime)
□ AARTIDRUGS.NS (extreme_volatility)
□ 63MOONS.NS    (extreme_illiquid)

For each stock:
□ Run: analyze_ticker(ticker, use_demo_data=False)
□ Store: Full JSON response
□ Record: Date, market_regime, score, verdict, confidence
□ Backup: Save to backup/ directory
```

### Step 0.3: Write Regression Tests
```bash
File: backend/tests/test_signal_snapshots.py

Test Functions:
□ test_score_unchanged()
  - Load snapshot
  - Run fresh analysis
  - Assert score == snapshot_score ± 0.01

□ test_verdict_unchanged()
  - Assert verdict == snapshot_verdict (exact match)

□ test_confidence_unchanged()
  - Assert confidence == snapshot_confidence ± 0.02

□ test_indicator_count()
  - Assert len(indicators) == 12

□ test_api_format_unchanged()
  - Assert all expected fields present
  - Assert no unexpected new fields
```

### Step 0.4: Update Script
```bash
File: backend/scripts/update_snapshots.py

Features:
□ Load current snapshots
□ Run analysis on all 10 stocks
□ Generate new snapshots
□ Display diff (old vs new)
□ Require manual approval
□ Back up old snapshots
□ Commit new snapshots

Usage:
python update_snapshots.py --review  (show diffs)
python update_snapshots.py --approve (commit new)
python update_snapshots.py --rollback (revert to backup)
```

---

## Phase 1: Category Metadata & Grouping

### Step 1.1: Create Metadata Registry
```bash
File: backend/utils/analysis/indicator_metadata.py

Structure:
□ INDICATOR_METADATA = {
    "RSI": { "category": "momentum", "description": "...", ... },
    "MACD": { "category": "trend", ... },
    ...
  }

□ CATEGORIES = {
    "momentum": { "indicators": 5, "weight": 0.8, ... },
    "trend": { "indicators": 4, "weight": 1.3, ... },
    "volatility": { "indicators": 2, "weight": 1.2, ... },
    "volume": { "indicators": 2, "weight": 1.5, ... },
  }

□ Import both in __init__.py
```

### Step 1.2: Create Grouper Functions
```bash
File: backend/utils/analysis/category_grouper.py

Functions:
□ group_indicators_by_category(indicator_results)
  Input: List of indicator dicts with 'name', 'vote', 'confidence'
  Output: Dict grouped by category
  Behavior: Read-only, no transformation, handle missing gracefully

□ calculate_category_summary(grouped_indicators)
  Input: Grouped indicators dict
  Output: Category-level stats (count, votes, confidences, averages)
  Behavior: Pure calculation, no side effects

□ get_category_metadata(indicator_name)
  Input: Indicator name
  Output: Metadata dict or None
  Behavior: Lookup helper
```

### Step 1.3: Write Unit Tests
```bash
File: backend/tests/test_category_metadata.py

Test Cases:
□ test_all_indicators_mapped()
  - Verify every indicator in ALL_INDICATORS has metadata

□ test_metadata_complete()
  - Verify each metadata entry has required fields

□ test_category_weights_valid()
  - Verify all weights >= 0, <= 2.0

□ test_grouper_preserves_data()
  - Run grouper on real indicator results
  - Verify no data loss
  - Verify all indicators still present

□ test_grouper_handles_unknown()
  - Pass indicator with name not in metadata
  - Verify graceful handling (defaults to "unknown" or skips)
  - Verify no crash

□ test_summary_math_correct()
  - Create known grouped indicators
  - Calculate summary
  - Verify averages manually

□ test_api_backward_compat()
  - Run orchestrator with Phase 1 code
  - Verify response format unchanged
  - Verify no breaking fields
```

### Step 1.4: Integration Point
```bash
File: backend/utils/analysis_orchestrator.py

Location: Inside AnalysisOrchestrator.analyze()
After: score = SignalAggregator.aggregate_votes(...)

Code:
□ from utils.analysis.category_grouper import group_indicators_by_category
□ from utils.analysis.category_grouper import calculate_category_summary

□ grouped = group_indicators_by_category(indicator_results)
□ category_summary = calculate_category_summary(grouped)

□ result['_phase1_metadata'] = {
     'grouped_indicators': grouped,
     'category_summary': category_summary
   }

Note: Uses '_' prefix to hide from UI (optional, internal only)
```

### Step 1.5: Configuration Flags
```bash
File: backend/config.py

Add:
□ PHASE1_METADATA_ENABLED = os.getenv('PHASE1_METADATA_ENABLED', 'true').lower() == 'true'

Wrap Step 1.4 with:
□ if PHASE1_METADATA_ENABLED:
     result['_phase1_metadata'] = {...}
```

---

## Testing Checklist

### Pre-Commit
```
□ pytest backend/tests/test_signal_snapshots.py -v
□ pytest backend/tests/test_category_metadata.py -v
□ pytest backend/tests/ -k "not integration" --cov=backend/utils/analysis
  (Target: > 95% coverage for new files)
```

### Integration
```
□ Run: python backend/simple_test.py
  Verify:
  - No errors
  - Same verdict as before
  - _phase1_metadata present (if PHASE1_METADATA_ENABLED=true)

□ Run: curl -s https://localhost:5000/results/RELIANCE.NS | jq .
  Verify:
  - score unchanged
  - verdict unchanged
  - confidence unchanged
  - No breaking changes
```

### Manual Verification
```
□ Test 5 different stocks
  - Check score is identical to snapshot
  - Check verdict is identical
  - Check new metadata is correct (grouping accurate)

□ Test with PHASE1_METADATA_ENABLED=false
  - Verify _phase1_metadata absent
  - Verify all other fields present
```

---

## Files to Create/Modify

### Create (NEW)
```
backend/utils/analysis/
  indicator_metadata.py          (200 lines)
  category_grouper.py            (150 lines)

backend/tests/
  test_signal_snapshots.py       (250 lines)
  test_category_metadata.py      (300 lines)

backend/scripts/
  update_snapshots.py            (200 lines)

backend/tests/snapshots/
  signal_snapshots.json          (auto-generated)
  backup/                        (directory)
```

### Modify (EXISTING)
```
backend/config.py
  - Add 2 new configuration flags

backend/utils/analysis_orchestrator.py
  - Add import statements
  - Add 5-6 lines in analyze() method
  - Maintain all existing behavior
```

### Documentation
```
CATEGORY_INTELLIGENCE_IMPLEMENTATION_PLAN.md  (this doc - 500+ lines)
CATEGORY_INTELLIGENCE_PHASES_01.md            (expanded Phase 0-1 details)
backend/utils/analysis/README.md              (update to document new modules)
```

---

## Rollback Plan

### If Phase 0 Fails
```bash
□ Delete backend/tests/snapshots/
□ Delete backend/tests/test_signal_snapshots.py
□ No changes to core logic = zero risk
```

### If Phase 1 Fails
```bash
□ Set PHASE1_METADATA_ENABLED = false
□ Delete _phase1_metadata from response
□ Delete new files:
  - indicator_metadata.py
  - category_grouper.py
  - test_category_metadata.py
□ System operates as before
```

### Always Available
```bash
□ git revert <commit_hash>
□ Instant rollback to previous state
```

---

## Success Criteria (Final)

### Phase 0 Success
- [ ] All 10 stocks snapshotted
- [ ] All 5 regression tests passing
- [ ] Snapshot update script working
- [ ] Can rollback and restore cleanly

### Phase 1 Success
- [ ] All indicators mapped to categories
- [ ] 12 indicators grouped correctly
- [ ] Summary calculations accurate
- [ ] Unit test coverage > 95%
- [ ] Zero breaking changes verified
- [ ] Backward compatibility 100%

### Combined Success
- [ ] All tests pass
- [ ] Snapshots unchanged (score, verdict, confidence)
- [ ] New metadata available (optional, unused)
- [ ] Ready for Phase 2
- [ ] Risk: MINIMAL
- [ ] Confidence: HIGH

---

## Git Commit Strategy

### Phase 0
```bash
git commit -m "Phase 0: Add snapshot test infrastructure and baselines

- Create snapshot tests for 10 stocks (3 market regimes)
- Store golden copy of current outputs
- Add regression test suite
- No logic changes - baseline safety lock

Tests passing: ✅ All 5 regression tests
Backward compat: ✅ 100% verified
Risk level: 🟢 MINIMAL
"
```

### Phase 1
```bash
git commit -m "Phase 1: Add category metadata and grouping (non-breaking)

- Create INDICATOR_METADATA registry
- Implement category_grouper.py
- Add calculate_category_summary()
- Attach _phase1_metadata to response (internal only)
- Add configuration flags

Tests passing: ✅ All 8 unit tests
Backward compat: ✅ 100% verified
API changes: ✅ Fully backward compatible
Risk level: 🟢 MINIMAL
"
```

---

## Timeline

```
Day 1 (Morning):  Phase 0 - Snapshots (4-5 hours)
Day 1 (Afternoon): Phase 1 - Metadata (3-4 hours)
Day 2 (Morning):  Final testing & documentation
Day 2 (Afternoon): Merge to main & deploy

Total: ~10 hours (1-2 days)
```

---

## Questions to Clarify Before Starting

1. **Snapshot Storage**: 
   - [ ] OK to store 10 stocks' full JSON responses in git?
   - [ ] Alternative: Store hashes only and regenerate on demand?

2. **Metadata Weights**:
   - [ ] Do the proposed weights look correct to you?
   - [ ] Any adjustments needed?

3. **Backward Compatibility**:
   - [ ] OK to add `_phase1_metadata` field to response?
   - [ ] Or should it be completely hidden (not in response)?

4. **Configuration**:
   - [ ] Should Phase 1 metadata be enabled by default (true)?
   - [ ] Or disabled until Phase 2 needs it (false)?

---

## Sign-Off

- [ ] Requirements approved
- [ ] Timeline acceptable  
- [ ] Risk mitigation understood
- [ ] Ready to start Phase 0
- [ ] Ready to start Phase 1

**Approved by**: _______________  **Date**: _______________
