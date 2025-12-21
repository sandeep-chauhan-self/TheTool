# Pre-Implementation Decision Guide

## Decision 1: Snapshot Storage Strategy

### Question
**Should we store full JSON responses in git, or only hashes?**

### Option A: Full JSON (Recommended)
**Pros:**
- ✅ Easy to understand what changed
- ✅ Can compare diffs visually
- ✅ Works with standard git tools
- ✅ Self-documenting (shows actual values)

**Cons:**
- ⚠️ Git repo slightly larger (~5-10 MB for 10 stocks)
- ⚠️ Need to update snapshots periodically (price changes)

**Decision**: ✅ **GO WITH FULL JSON**

**Rationale**: Visibility and debuggability are worth the minor repo size cost. If snapshots get stale, we just re-run the update script.

**Implementation**:
```json
backend/tests/snapshots/signal_snapshots.json
{
  "RELIANCE.NS": {
    "date_captured": "2025-12-21T10:00:00Z",
    "market_regime": "bullish",
    "full_response": {
      "score": 0.75,
      "verdict": "Buy",
      ...
    }
  }
}
```

---

### Option B: Hash-Only (Alternative)
**Pros:**
- ✅ Tiny repo footprint
- ✅ Snapshots never stale

**Cons:**
- ❌ Less visible what changed
- ❌ Harder to debug test failures
- ❌ Need separate archive for full responses

**Decision**: ❌ **NOT RECOMMENDED FOR NOW**

---

## Decision 2: Metadata Weights

### Current Proposal
```python
TYPE_BIAS = {
    "volume": 1.5,      # Most important
    "trend": 1.3,       # Strong confirmation
    "volatility": 1.2,  # Risk management
    "momentum": 0.8,    # Lagging signals
}
```

### Rationale (Why This Order)

#### Volume = 1.5 (Highest)
- **Why**: Volume LEADS price (most predictive)
- **Example**: High volume break above resistance is more reliable than RSI signal
- **Risk if wrong**: If we under-weight volume, we might chase breakouts with low volume
- **Impact**: Filters out weak moves

#### Trend = 1.3 (Second Highest)
- **Why**: Trend is the primary direction
- **Example**: ADX + MACD agreement = clear directional bias
- **Risk if wrong**: Over-weighting trend means we miss reversals
- **Impact**: Ensures we're trading the right direction

#### Volatility = 1.2 (Third)
- **Why**: Volatility controls risk and position sizing
- **Example**: High ATR means use wider stops
- **Risk if wrong**: Ignoring volatility = blowing up on wide moves
- **Impact**: Risk management, not trade entry

#### Momentum = 0.8 (Lowest)
- **Why**: Momentum is LAGGING (already priced in)
- **Example**: RSI at 95 is already overbought - momentum is fading
- **Risk if wrong**: Over-weighting momentum = jumping on tired moves
- **Impact**: Still useful for confirming, but not as primary signal

### Question
**Do these weights align with your trading experience?**

### Options

#### Option A: Accept Proposed Weights (Recommended)
```python
TYPE_BIAS = {
    "volume": 1.5,
    "trend": 1.3,
    "volatility": 1.2,
    "momentum": 0.8
}
```
**Decision**: ✅ **RECOMMENDED** - Aligns with professional trading wisdom

---

#### Option B: Adjust Weights
```python
# If you prefer momentum stronger:
TYPE_BIAS = {
    "volume": 1.5,
    "trend": 1.2,
    "momentum": 1.0,    # Boost momentum
    "volatility": 1.0
}

# If you prefer more conservative (volume + risk):
TYPE_BIAS = {
    "volume": 2.0,      # Super aggressive on volume
    "trend": 1.0,
    "volatility": 1.5,  # Higher risk tolerance
    "momentum": 0.5
}
```
**Decision**: Choose based on your trading philosophy

---

#### Option C: Use Strategy-Specific Weights
```python
# Let each strategy define its own weights

# Strategy 5 (Momentum-focused):
TYPE_BIAS = {
    "momentum": 2.0,    # DOMINANT
    "volatility": 1.0,
    "trend": 0.5,
    "volume": 0.9
}

# Strategy 1 (Balanced):
TYPE_BIAS = {
    "trend": 1.3,
    "volume": 1.5,
    "volatility": 1.0,
    "momentum": 0.8
}
```
**Decision**: More flexible, but requires more setup

---

### Recommendation
**→ Start with Option A (proposed weights)**
- Lock in these for Phase 2
- Can adjust after we see real performance data
- Can evolve to Option C later if needed

---

## Decision 3: Metadata Visibility

### Question
**Should `_phase1_metadata` be visible in API response, or hidden?**

### Option A: Include in Response (Fully Visible)
```json
{
  "score": 0.75,
  "verdict": "Buy",
  "confidence": 0.82,
  
  "_phase1_metadata": {
    "grouped_indicators": { ... },
    "category_summary": { ... }
  }
}
```

**Pros:**
- ✅ Frontend can immediately use this for UI enhancements
- ✅ Clients see the metadata structure
- ✅ Transparent and inspectable

**Cons:**
- ⚠️ Slightly larger API response (~2-3 KB per request)
- ⚠️ Old clients might not recognize `_phase1_*` fields

**Decision**: ✅ **RECOMMENDED - Include in response**

---

### Option B: Hidden (Internal Only)
```python
# Inside backend only, never sent to frontend
if PHASE1_METADATA_ENABLED:
    internal_metadata = {
        "grouped_indicators": grouped,
        "category_summary": category_summary
    }
    # Used by Phase 2+ but not sent to API
```

**Pros:**
- ✅ Minimal API response size
- ✅ Clean, focused API contract

**Cons:**
- ❌ Frontend can't use it until Phase 3+
- ❌ More complex internal plumbing

**Decision**: ❌ **NOT RECOMMENDED FOR NOW**

---

### Recommendation
**→ Option A: Include in response**
- Rationale: We want frontend developers to see this data
- Prefix with `_phase1_` to signal "internal/experimental"
- Phase 2 can make it production-ready

---

## Decision 4: Configuration Default

### Question
**Should `PHASE1_METADATA_ENABLED` default to `true` or `false`?**

### Option A: Enabled by Default (true)
```python
PHASE1_METADATA_ENABLED = os.getenv('PHASE1_METADATA_ENABLED', 'true').lower() == 'true'
```

**Pros:**
- ✅ Metadata always available (no extra config needed)
- ✅ Developers see it immediately
- ✅ Prepares for Phase 2

**Cons:**
- ⚠️ Small response size increase

**Decision**: ✅ **RECOMMENDED - Enable by default**

---

### Option B: Disabled by Default (false)
```python
PHASE1_METADATA_ENABLED = os.getenv('PHASE1_METADATA_ENABLED', 'false').lower() == 'true'
```

**Pros:**
- ✅ Zero overhead if not needed
- ✅ Opt-in for new features

**Cons:**
- ❌ Harder to discover the feature
- ❌ Extra configuration step for Phase 2

**Decision**: ❌ **NOT RECOMMENDED**

---

### Recommendation
**→ Option A: Enabled by default**
- Rationale: Safe change, small overhead, prepares for Phase 2
- Can disable with `export PHASE1_METADATA_ENABLED=false`

---

## Decision 5: Snapshot Update Frequency

### Question
**How often should we re-run snapshot updates?**

### Options

#### Option A: Manual (On-Demand)
```bash
python backend/scripts/update_snapshots.py --review
# Only when we intentionally change behavior
```

**Pros:**
- ✅ Full control
- ✅ Explicit approval for changes

**Cons:**
- ⚠️ Snapshots get stale (prices change daily)
- ⚠️ Regression test might fail due to outdated data

**Decision**: ⚠️ **USE FOR DEVELOPMENT**

---

#### Option B: Weekly Automated
```bash
# CI/CD schedule: Every Monday 00:00 UTC
python backend/scripts/update_snapshots.py --approve
git push origin development
```

**Pros:**
- ✅ Snapshots stay current
- ✅ Less maintenance

**Cons:**
- ❌ Might mask bugs if prices move significantly

**Decision**: ⚠️ **USE FOR PRODUCTION**

---

#### Option C: Per-Commit (Dev) + Weekly (Prod)
```
Development:  Manual updates (on-demand)
Staging:      Weekly automated
Production:   Quarterly manual reviews
```

**Decision**: ✅ **RECOMMENDED - Hybrid approach**

---

### Recommendation
**→ Option C: Hybrid (Manual + Scheduled)**
- Start: Manual updates during Phase 0-1
- Later: Set up CI/CD schedule for production

---

## Decision 6: Snapshot Retention Policy

### Question
**How many backup versions should we keep?**

### Options

#### Option A: Keep All (VCS Only)
```
snapshots/
├── signal_snapshots.json
└── Git history (all versions)
```

**Pros:**
- ✅ Complete audit trail
- ✅ Can recover any version

**Cons:**
- ⚠️ Git history grows

---

#### Option B: Keep Last 5
```
snapshots/
├── signal_snapshots.json
└── backup/
    ├── 2025-12-21.json
    ├── 2025-12-14.json
    ├── 2025-12-07.json
    ├── 2025-11-30.json
    └── 2025-11-23.json
```

**Decision**: ✅ **RECOMMENDED**
- Rational: Balance between space and history
- Use: `keep_last(5)` in update script

---

#### Option C: Keep Last 1 + All in Git
```
snapshots/
├── signal_snapshots.json (current)
└── backup/
    └── previous.json (last version only)
```

**Decision**: ⚠️ **ACCEPTABLE ALTERNATIVE**

---

### Recommendation
**→ Option B: Keep last 5 backups + git history**
- Allows rollback without git gymnastics
- Manageable disk usage
- Good compromise

---

## Summary of Recommendations

| Decision | Recommendation | Impact |
|----------|---------------|--------|
| Snapshot Storage | Full JSON in git | ✅ |
| Metadata Weights | Proposed (V: 1.5, T: 1.3, Vol: 1.2, M: 0.8) | ✅ |
| Metadata Visibility | Include as `_phase1_metadata` in response | ✅ |
| Config Default | `PHASE1_METADATA_ENABLED = true` | ✅ |
| Snapshot Updates | Manual (dev) + weekly (prod) | ✅ |
| Backup Retention | Keep last 5 + git history | ✅ |

---

## Final Checklist Before Starting

- [ ] Decision on all 6 items above
- [ ] Weights approved by user
- [ ] Timeline confirmed acceptable
- [ ] Risk mitigation understood
- [ ] Ready to begin Phase 0 tomorrow

**→ If all checked, proceed to PHASE_0_1_QUICK_REFERENCE.md**
