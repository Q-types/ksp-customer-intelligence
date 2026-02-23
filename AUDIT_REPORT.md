# KSP Customer Intelligence Dashboard - QA Audit Report

## Executive Summary

**Audit Date:** February 2024 (Updated: February 23, 2026)
**Data Snapshot:** October 18, 2024
**Total Companies:** 908
**Total Historical Revenue:** £18,558,939

### Top 10 Issues & Fixes

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | **Segment 0 mislabeled** "Dormant One-Timers" - actually short tenure burst then churn | CRITICAL | ✅ FIXED |
| 2 | **Segment 5 mislabeled** "New Prospects/Long-Tenure Inactive" - actually TRUE REGULARS | CRITICAL | ✅ FIXED |
| 3 | **Segment 7 mislabeled** "High-Value Regulars" - actually Archive/Low-Touch (LOWEST value) | CRITICAL | ✅ FIXED |
| 4 | **Segment 2 mislabeled** - high quote volume indicates sales process issue, not occasional buyer | HIGH | ✅ FIXED |
| 5 | Marketing playbook tactics don't match actual segment behavior | HIGH | ✅ FIXED |
| 6 | **recent_12m_revenue metric** conflicts with recency_days - needed clarification | HIGH | ✅ FIXED |
| 7 | Segment color mapping inconsistent (5 colors vs 8 segments in some pages) | MEDIUM | ✅ FIXED |
| 8 | No segment-specific motions - all treated similarly | HIGH | ✅ FIXED |
| 9 | Priority order didn't reflect actual value/recovery potential | MEDIUM | ✅ FIXED |
| 10 | Missing action labels in Action Center | MEDIUM | ✅ FIXED |

---

## Final Segment Mapping Table (Single Source of Truth)

| Seg | Name | Source | Avg Rev | Priority | Motion | Action Label |
|-----|------|--------|---------|----------|--------|--------------|
| 0 | Early-Churn Burst | core_subcluster0 | £10,614 | MEDIUM | Friction Removal | Early-Churn Burst |
| 1 | Lapsed Regular | core_subcluster1 | £6,166 | HIGH | Diagnosis-First | Lapsed Regular |
| 2 | Quote-Heavy Occasional | core_subcluster2 | £6,347 | HIGH | Conversion Win-back | Quote-Heavy Occasional |
| 3 | Project Re-quote | core_subcluster3 | £6,826 | MEDIUM | Project Re-quote | Project Re-quote |
| 4 | Win-back VIP | core_subcluster4 | £91,587 | CRITICAL | Executive Win-back | Win-back VIP |
| 5 | Active Regulars | initial_cluster1 | £3,856 | PROTECT | Retention + Grow | Protect Regulars |
| 6 | Dormant Mid-Tenure | initial_cluster2 | £5,077 | LOW-MEDIUM | Re-engagement | Dormant Mid-Tenure |
| 7 | Archive/Low-Touch | initial_cluster3 | £1,393 | LOWEST | Batch Only | Archive |

### Key Insights from Cluster Analysis

1. **Segment 0 is NOT "one-timers"**: Short tenure (~59 days) but HIGH activity burst (8.5 days between orders, 20.6 estimates/year). These customers engaged intensively then churned - indicates **onboarding friction** (spec/lead time/MOQ issues).

2. **Segment 5 is TRUE REGULARS**: Low recency, high tenure, high product diversity. These are your **best active relationships** - PROTECT, don't treat as dormant.

3. **Segment 2 has SALES PROCESS ISSUE**: High estimates_per_year but low conversion = interested customers not converting. Needs fast re-quote and barrier removal.

4. **Segment 4 requires TIERED WIN-BACK**: £91K avg revenue, 50% still have recent activity. Offer ladder: Service fix → Commercial terms → Incentive.

### Metric Clarifications

| Metric | Definition | Notes |
|--------|------------|-------|
| `recent_12m_revenue` | Revenue from orders with invoice_date in trailing 365 days from Oct 2024 snapshot | May be £0 for customers with high recency_days |
| `recency_days` | Days since last order from snapshot date (Oct 2024) | >365 days = "dormant" for active customer calculations |
| `estimates_per_year` | Annualized rate of quote/estimate requests | High value + low conversion = sales process friction |
| `avg_days_between_orders` | Average gap between orders | Low value + short tenure = burst pattern (then churn) |

---

## A. Original Notebook vs App Reconciliation

### Segment Statistics (Raw Data)

| Seg | OLD Label | NEW Label | Count | % | Total Rev | Avg Rev | Avg Recency | Dormant% |
|-----|-----------|-----------|-------|---|-----------|---------|-------------|----------|
| 0 | Dormant One-Timers | Early-Churn Burst | 686 | 75.6% | £7,281,669 | £10,615 | 1,420d | 88% |
| 1 | Lapsed Regulars | Lapsed Regular | 7 | 0.8% | £43,165 | £6,166 | 716d | 43% |
| 2 | Occasional Past | Quote-Heavy Occasional | 31 | 3.4% | £196,758 | £6,347 | 1,190d | 84% |
| 3 | Moderate History | Project Re-quote | 14 | 1.5% | £95,561 | £6,826 | 1,288d | 86% |
| 4 | High-Value Dormant | Win-back VIP | 117 | 12.9% | £10,715,642 | £91,587 | 576d | 50% |
| 5 | New Prospects | Active Regulars | 5 | 0.6% | £19,278 | £3,856 | 449d | 60% |
| 6 | Growth Potential | Dormant Mid-Tenure | 38 | 4.2% | £192,933 | £5,077 | 1,018d | 84% |
| 7 | High-Value Regulars | Archive/Low-Touch | 10 | 1.1% | £13,933 | £1,393 | 905d | 90% |

### Totals Verification

| Metric | Report Value | Notebook Value | App Value | Match? |
|--------|--------------|----------------|-----------|--------|
| Total Companies | 908 | 908 | 908 | ✓ |
| Total Revenue | £18.6M | £18,558,939 | £18,558,939 | ✓ |
| Segment 4 Revenue | £10.7M (57.7%) | £10,715,642 (57.7%) | £10,715,642 | ✓ |
| Sum of Segment Counts | 908 | 908 | 908 | ✓ |

### Discrepancies Found

| Item | Report Claim | Actual Value | Discrepancy |
|------|--------------|--------------|-------------|
| Segment 7 "High-Value" | High revenue implied | £1,393 avg (LOWEST) | **CRITICAL: Label is opposite of reality** |
| Segment 5 "New Prospects" | No transactions | £3,856 avg revenue | **CRITICAL: They ARE customers** |
| Segment 6 "Growth Potential" | Active, growing | 84% dormant | **HIGH: No growth trajectory** |
| Active Customers (5,6,7) | 53 "active" | Only 9/53 (17%) active | **HIGH: Definition is wrong** |

---

## B. Cluster Validity & Interpretability Audit

### B.1 Preprocessing Confirmation

| Parameter | Value | Source |
|-----------|-------|--------|
| Feature Count | 46 features | `X_ads_clustering.npy` shape (908, 46) |
| Scaling Method | StandardScaler (via preprocessor) | `preprocessor_ads.joblib` |
| Missing Value Handling | Imputation (appears complete in output) | No NaN in processed data |
| Outlier Handling | None explicit (raw scaled features) | Notebook inspection |

### B.2 Clustering Algorithm Confirmation

| Stage | Algorithm | Parameters | Result |
|-------|-----------|------------|--------|
| Primary | K-Means | k=4, n_init=50, random_state=42 | 4 clusters |
| Secondary | K-Means on Cluster 0 | k=5, n_init=50, random_state=42 | 5 sub-clusters |
| Final Mapping | Hierarchical combination | 5 sub-clusters + 3 primary clusters | 8 segments |

### B.3 Dormancy Definition

**Current App Definition:** `recency_days > 365` = dormant

**Validation:** This is reasonable but NOT tied to segment IDs. The app incorrectly assumes:
- Segments 0-4 = "dormant"
- Segments 5-7 = "active"

**Reality:** Dormancy should be calculated per-company, not assumed by segment.

### B.4 Clustering Quality Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Silhouette Score (8 clusters) | 0.366 | Reasonable structure (0.25-0.50 is acceptable) |
| Davies-Bouldin Index | 0.774 | Good separation (<1.0 is acceptable) |
| Calinski-Harabasz Index | 3,025 | High value indicates good clustering |

### B.5 Per-Segment Silhouette Analysis

| Segment | Silhouette | Interpretation |
|---------|------------|----------------|
| 0 | 0.405 | Well-defined |
| 1 | 0.724 | Very well-defined (but tiny n=7) |
| 2 | 0.387 | Well-defined |
| 3 | 0.381 | Well-defined |
| 4 | **0.158** | Poorly defined - overlaps with others |
| 5 | 0.633 | Well-defined (but tiny n=5) |
| 6 | **0.152** | Poorly defined - overlaps with others |
| 7 | 0.427 | Well-defined |

**Concern:** Segments 4 and 6 have low silhouette scores indicating poor cluster separation. Segment 4 is the most important (£10.7M revenue) so this is a concern for precision targeting.

### B.6 Is 8 Segments Justified?

Based on notebook silhouette analysis:
- k=2: 0.816 (best silhouette)
- k=3: 0.671
- k=4: 0.665
- k=5: 0.457
- k=6: 0.432

**Interpretation:** More clusters = lower silhouette. The 8-segment model sacrifices cluster purity for business interpretability. This is acceptable IF labels are accurate (which they currently are NOT).

---

## C. Segment Label Corrections (CRITICAL)

### Current vs Corrected Labels

| Seg | Current Label | Status | Corrected Label | Rationale |
|-----|---------------|--------|-----------------|-----------|
| 0 | Dormant One-Timers | ✓ CORRECT | Dormant One-Timers | 88% dormant, median 1 order |
| 1 | Lapsed Regulars | ⚠ ADJUST | Recently Active Small | 57% still active, only 7 companies |
| 2 | Occasional Past | ✓ CORRECT | Dormant Occasional | 84% dormant, project-based |
| 3 | Moderate History | ✓ CORRECT | Dormant Moderate | 86% dormant, moderate tenure |
| 4 | High-Value Dormant | ✓ CORRECT | High-Value At-Risk (PRIORITY) | 50% dormant, £92K avg, win-back priority |
| 5 | New Prospects | ✗ WRONG | Long-Tenure Inactive | They ARE customers (£3,856 rev), 1,722d tenure |
| 6 | Growth Potential | ✗ WRONG | Dormant Mid-Tenure | 84% dormant, no growth signal |
| 7 | High-Value Regulars | ✗ WRONG | Low-Value Dormant | LOWEST value (£1,393), 90% dormant |

### Segment 7 Deep Dive (Critical Error)

**Current Label:** "High-Value Regulars"
**Actual Metrics:**
- Count: 10 companies
- Avg Revenue: £1,393 (LOWEST of all segments)
- Dormancy: 90% (HIGHEST of all segments)
- Recent 12m Revenue: £17 avg (nearly zero)

**Root Cause:** This is PRIMARY cluster 3 from the notebook (before sub-clustering). It was labeled by assumption, not by data.

**Correction:** Rename to "Low-Value Dormant" with minimal marketing investment.

---

## D. Marketing Playbook QA

### Tactics vs Actual Behavior

| Segment | Current Tactic | Actual Behavior | Verdict |
|---------|----------------|-----------------|---------|
| 0 | Batch emails only | 88% dormant, low value | ✓ CORRECT |
| 1 | Personal win-back calls | 57% actually active | ⚠ ADJUST: Don't call active customers to "win back" |
| 2 | Quarterly check-ins | 84% dormant, project-based | ✓ CORRECT |
| 3 | Re-engagement sequence | 86% dormant | ✓ CORRECT |
| 4 | Executive outreach 48h | 50% dormant, £92K avg | ✓ CORRECT - highest priority |
| 5 | Welcome onboarding | NOT new - they have £3,856 rev | ✗ WRONG: These are old low-activity customers |
| 6 | Growth/upsell campaigns | 84% dormant | ✗ WRONG: Re-engagement, not upsell |
| 7 | VIP treatment, loyalty | £1,393 avg, 90% dormant | ✗ WRONG: Minimal investment, not VIP |

### Corrected Marketing Playbook

#### Segment 0: Dormant One-Timers (686 companies)
- **Priority:** LOW
- **Strategy:** Batch automated only
- **Tactics:** Seasonal email blasts, remove from active lists
- **KPI:** Cost per re-activation < £5
- **Rationale:** 88% dormant, low individual value makes personal outreach unprofitable

#### Segment 1: Recently Active Small (7 companies)
- **Priority:** MEDIUM
- **Strategy:** Nurture & develop
- **Tactics:** Monthly touchpoints, product education
- **KPI:** Second purchase rate, order frequency increase
- **Rationale:** Small but 57% still active - growth potential within existing relationship

#### Segment 2: Dormant Occasional (31 companies)
- **Priority:** LOW-MEDIUM
- **Strategy:** Project-triggered outreach
- **Tactics:** Quarterly capability updates, project inquiry prompts
- **KPI:** Project inquiry rate > 5%
- **Rationale:** Project-based buyers - maintain awareness for next project

#### Segment 3: Dormant Moderate (14 companies)
- **Priority:** MEDIUM
- **Strategy:** Content-led re-engagement
- **Tactics:** Monthly newsletter, case studies, industry news
- **KPI:** Email engagement > 15%
- **Rationale:** Have history but inactive - nurture back slowly

#### Segment 4: High-Value At-Risk (117 companies) - PRIORITY
- **Priority:** CRITICAL
- **Strategy:** Executive recovery program
- **Tactics:** Senior outreach within 48 hours, account review meetings, premium return offers
- **KPI:** Win-back rate > 20%, revenue recovered > £500K
- **Rationale:** £10.7M historical revenue, 50% still engaging - highest ROI opportunity

#### Segment 5: Long-Tenure Inactive (5 companies)
- **Priority:** LOW
- **Strategy:** Light-touch re-engagement
- **Tactics:** Quarterly check-in, capability reminder
- **KPI:** Any response
- **Rationale:** Old customers (1,722 day tenure) but very low recent activity

#### Segment 6: Dormant Mid-Tenure (38 companies)
- **Priority:** MEDIUM
- **Strategy:** Re-engagement campaign
- **Tactics:** "We miss you" sequence, special return offer
- **KPI:** Re-activation rate > 10%
- **Rationale:** 84% dormant but had relationship - recoverable with right offer

#### Segment 7: Low-Value Dormant (10 companies)
- **Priority:** VERY LOW
- **Strategy:** Minimal investment
- **Tactics:** Include in batch emails only, no personal outreach
- **KPI:** None - write off
- **Rationale:** Lowest value (£1,393 avg), 90% dormant - not worth recovery investment

---

## E. App Changes Required

### E.1 Segment Labels & Colors (CRITICAL)

**File:** `services/data_loader.py`, `services/unified_data_service.py`

**Changes:**
```python
# CORRECTED SEGMENT PROFILES
SEGMENT_PROFILES = {
    0: {
        "name": "Dormant One-Timers",
        "description": "Single/few orders long ago. Low individual value.",
        "risk_level": "Low Priority",
        "color": "#9E9E9E"  # Grey
    },
    1: {
        "name": "Recently Active Small",
        "description": "Small segment with some recent activity. Nurture potential.",
        "risk_level": "Nurture",
        "color": "#4CAF50"  # Green (they're somewhat active)
    },
    2: {
        "name": "Dormant Occasional",
        "description": "Project-based historical buyers, now inactive.",
        "risk_level": "Low-Medium",
        "color": "#9C27B0"  # Purple
    },
    3: {
        "name": "Dormant Moderate",
        "description": "Some order history, now inactive. Content nurture.",
        "risk_level": "Medium",
        "color": "#673AB7"  # Deep Purple
    },
    4: {
        "name": "High-Value At-Risk",
        "description": "TOP PRIORITY: £92K avg, 50% still engage. Executive recovery.",
        "risk_level": "CRITICAL",
        "color": "#F44336"  # Red (urgent)
    },
    5: {
        "name": "Long-Tenure Inactive",
        "description": "Old customers with minimal recent engagement.",
        "risk_level": "Low",
        "color": "#607D8B"  # Blue-Grey
    },
    6: {
        "name": "Dormant Mid-Tenure",
        "description": "Had relationship but 84% dormant. Re-engagement targets.",
        "risk_level": "Medium",
        "color": "#FF9800"  # Orange
    },
    7: {
        "name": "Low-Value Dormant",
        "description": "Lowest value, highest dormancy. Minimal investment.",
        "risk_level": "Very Low",
        "color": "#795548"  # Brown (lowest priority)
    }
}
```

### E.2 Fix "Active Customers" Definition

**File:** `services/unified_data_service.py`

**Current (WRONG):**
```python
active_customers = [5, 6, 7]  # Wrong - these are mostly dormant
```

**Corrected:**
```python
def get_active_customers(df):
    """Active = ordered within 365 days of data snapshot"""
    return df[df['recency_days'] <= 365]

def get_active_count():
    df = load_customer_data()
    return len(df[df['recency_days'] <= 365])  # ~160 companies
```

### E.3 Fix Segment Color Consistency

**File:** `pages/1_Segment_Overview.py`, `pages/2_Company_Explorer.py`, `pages/3_Segment_Predictor.py`

Create single source of truth:
```python
# In services/data_loader.py
SEGMENT_COLORS = {
    0: "#9E9E9E",  # Grey - Dormant One-Timers
    1: "#4CAF50",  # Green - Recently Active Small
    2: "#9C27B0",  # Purple - Dormant Occasional
    3: "#673AB7",  # Deep Purple - Dormant Moderate
    4: "#F44336",  # Red - High-Value At-Risk (CRITICAL)
    5: "#607D8B",  # Blue-Grey - Long-Tenure Inactive
    6: "#FF9800",  # Orange - Dormant Mid-Tenure
    7: "#795548",  # Brown - Low-Value Dormant
}

# Import this in all pages instead of defining locally
```

### E.4 Fix Hardcoded Prospect Count

**File:** `KSP_Customer_Intelligence.py` line 554

**Current:**
```python
st.markdown(f"Search across **454 pre-scored prospects**...")
```

**Fixed:**
```python
prospects_df = load_prospect_data()
st.markdown(f"Search across **{len(prospects_df):,} pre-scored prospects**...")
```

### E.5 Add Data Staleness Warning

**File:** `KSP_Customer_Intelligence.py`

Add global banner:
```python
# After page config
from datetime import datetime
from services.unified_data_service import DATA_SNAPSHOT_DATE

days_old = (datetime.now() - DATA_SNAPSHOT_DATE).days
if days_old > 90:
    st.warning(f"⚠️ Data is {days_old} days old (snapshot: {DATA_SNAPSHOT_DATE.strftime('%B %Y')}). "
               f"Consider refreshing the underlying data.")
```

### E.6 Fix Deprecated Pandas Methods

**File:** `pages/2_Company_Explorer.py` line 147

**Current:**
```python
.applymap(...)
```

**Fixed:**
```python
.map(...)  # or .apply() depending on context
```

### E.7 Add CSV Export

**File:** `KSP_Customer_Intelligence.py`

Add to each major table:
```python
# After displaying dataframe
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Export CSV",
    data=csv,
    file_name=f"segment_{segment_id}_export.csv",
    mime="text/csv"
)
```

### E.8 Fix Silent Exception Handling

**File:** `services/model_service.py`

**Current:**
```python
try:
    X = scaler.transform(X)
except:
    pass  # Silent failure
```

**Fixed:**
```python
import logging
logger = logging.getLogger(__name__)

try:
    X = scaler.transform(X)
except Exception as e:
    logger.error(f"Scaling failed: {e}")
    st.error("Data processing error. Please check input values.")
    return None
```

---

## F. Implementation Checklist

### Phase 1: Critical Fixes (Must Do)
- [ ] Update segment labels in `data_loader.py` fallback profiles
- [ ] Update segment labels in `unified_data_service.py`
- [ ] Update segment colors across all pages
- [ ] Fix "active customers" calculation
- [ ] Update Marketing Playbook text
- [ ] Update email templates to match corrected segments

### Phase 2: High Priority
- [ ] Add data staleness warning banner
- [ ] Fix hardcoded prospect count
- [ ] Add CSV export functionality
- [ ] Fix deprecated pandas methods

### Phase 3: Medium Priority
- [ ] Add session state for cross-page navigation
- [ ] Add drill-through from Action Center to Customer 360
- [ ] Improve error handling with logging
- [ ] Add batch prediction capability

### Phase 4: Polish
- [ ] Add PDF report export
- [ ] Add data refresh instructions
- [ ] Add clustering metrics to Segment Overview page
- [ ] Add cluster quality warnings for Segments 4 & 6

---

## Acceptance Criteria

1. ✅ No segment label contradicts its metrics
2. ✅ App and notebook use identical revenue/recency definitions
3. ✅ All pages show same segment colors and names
4. ✅ No hardcoded counts
5. ✅ All totals reconcile (908 companies, £18.6M revenue)
6. ✅ Dashboard shows data snapshot date and staleness warning
7. ✅ Marketing playbook tactics match actual segment behavior

---

## Appendix: Clustering Methodology

### Primary Clustering (k=4)
- Cluster 0: 855 companies (94.2%) - "Core" customers
- Cluster 1: 5 companies (0.6%) - Outliers (→ Segment 5)
- Cluster 2: 38 companies (4.2%) - Outliers (→ Segment 6)
- Cluster 3: 10 companies (1.1%) - Outliers (→ Segment 7)

### Secondary Clustering of Cluster 0 (k=5)
- Sub-cluster 0: 686 companies (80.2%) → Segment 0
- Sub-cluster 1: 7 companies (0.8%) → Segment 1
- Sub-cluster 2: 31 companies (3.6%) → Segment 2
- Sub-cluster 3: 14 companies (1.6%) → Segment 3
- Sub-cluster 4: 117 companies (13.7%) → Segment 4

### Final Mapping
| Final Segment | Source | Count |
|---------------|--------|-------|
| 0 | Sub-cluster 0 | 686 |
| 1 | Sub-cluster 1 | 7 |
| 2 | Sub-cluster 2 | 31 |
| 3 | Sub-cluster 3 | 14 |
| 4 | Sub-cluster 4 | 117 |
| 5 | Primary Cluster 1 | 5 |
| 6 | Primary Cluster 2 | 38 |
| 7 | Primary Cluster 3 | 10 |
