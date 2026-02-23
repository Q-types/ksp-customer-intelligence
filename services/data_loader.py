"""
Data Loading Service
Handles loading and caching of all data files

SEGMENT MAPPING (Single Source of Truth)
=========================================
Segments 0-4: ADS Core Recluster (subclusters of initial mixed cluster 0)
Segments 5-7: Original primary clusters 1, 2, 3 (remapped)

Final Mapping Table:
| Segment | Source           | Name                    | Avg Value | Priority    | Motion               |
|---------|------------------|-------------------------|-----------|-------------|----------------------|
| 0       | core_subcluster0 | Early-Churn Burst       | £10,614   | MEDIUM      | Friction removal     |
| 1       | core_subcluster1 | Lapsed Regular          | £6,166    | HIGH        | Diagnosis-first      |
| 2       | core_subcluster2 | Quote-Heavy Occasional  | £6,347    | HIGH        | Conversion win-back  |
| 3       | core_subcluster3 | Project Re-quote        | £6,826    | MEDIUM      | Semi-personal        |
| 4       | core_subcluster4 | Win-back VIP            | £91,587   | CRITICAL    | Executive win-back   |
| 5       | initial_cluster1 | Active Regulars         | £3,856    | PROTECT     | Retention + grow     |
| 6       | initial_cluster2 | Dormant Mid-Tenure      | £5,077    | LOW-MEDIUM  | Re-engagement        |
| 7       | initial_cluster3 | Archive/Low-Touch       | £1,393    | LOWEST      | Batch only           |

METRIC NOTES:
- recent_12m_revenue: Computed from orders with invoice_date in trailing 365 days from
  snapshot date (Oct 2024). May show £0 for customers with high recency_days.
- recency_days: Days since last order from snapshot date.
- estimates_per_year: Annual rate of quote requests (indicates engagement/intent).
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Base paths - using local data within dashboard for standalone deployment
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "companies"
MODELS_DIR = BASE_DIR / "models" / "customer_segments"
OUTPUTS_DIR = BASE_DIR / "outputs" / "segmentation"

# =============================================================================
# SEGMENT CONFIGURATION - SINGLE SOURCE OF TRUTH
# =============================================================================

SEGMENT_CONFIG = {
    0: {
        "name": "Early-Churn Burst",
        "short_name": "Burst Churn",
        "source": "core_subcluster0",
        "color": "#FF7043",  # Deep Orange - onboarding friction
        "priority": "MEDIUM",
        "priority_rank": 3,
        "motion": "Friction Removal",
        "action_label": "Early-Churn Burst",
        "is_active": False,  # Behavior-based: recency > 365
    },
    1: {
        "name": "Lapsed Regular",
        "short_name": "Lapsed",
        "source": "core_subcluster1",
        "color": "#AB47BC",  # Purple - diagnosis needed
        "priority": "HIGH",
        "priority_rank": 2,
        "motion": "Diagnosis-First",
        "action_label": "Lapsed Regular",
        "is_active": False,
    },
    2: {
        "name": "Quote-Heavy Occasional",
        "short_name": "Quote-Heavy",
        "source": "core_subcluster2",
        "color": "#5C6BC0",  # Indigo - sales process issue
        "priority": "HIGH",
        "priority_rank": 2,
        "motion": "Conversion Win-back",
        "action_label": "Quote-Heavy Occasional",
        "is_active": False,
    },
    3: {
        "name": "Project Re-quote",
        "short_name": "Project",
        "source": "core_subcluster3",
        "color": "#26A69A",  # Teal - project-based
        "priority": "MEDIUM",
        "priority_rank": 3,
        "motion": "Project Re-quote",
        "action_label": "Project Re-quote",
        "is_active": False,
    },
    4: {
        "name": "Win-back VIP",
        "short_name": "VIP",
        "source": "core_subcluster4",
        "color": "#E53935",  # Red - CRITICAL
        "priority": "CRITICAL",
        "priority_rank": 1,
        "motion": "Executive Win-back",
        "action_label": "Win-back VIP",
        "is_active": False,  # 50% still have recent_12m_revenue
    },
    5: {
        "name": "Active Regulars",
        "short_name": "Regulars",
        "source": "initial_cluster1",
        "color": "#43A047",  # Green - PROTECT
        "priority": "PROTECT",
        "priority_rank": 1,
        "motion": "Retention + Grow",
        "action_label": "Protect Regulars",
        "is_active": True,  # Low recency, high tenure, high diversity
    },
    6: {
        "name": "Dormant Mid-Tenure",
        "short_name": "Mid-Dormant",
        "source": "initial_cluster2",
        "color": "#FFA726",  # Orange - re-engagement
        "priority": "LOW-MEDIUM",
        "priority_rank": 4,
        "motion": "Re-engagement",
        "action_label": "Dormant Mid-Tenure",
        "is_active": False,
    },
    7: {
        "name": "Archive/Low-Touch",
        "short_name": "Archive",
        "source": "initial_cluster3",
        "color": "#78909C",  # Blue Grey - lowest priority
        "priority": "LOWEST",
        "priority_rank": 5,
        "motion": "Batch Only",
        "action_label": "Archive",
        "is_active": False,
    },
}

# Derived mappings for backward compatibility
SEGMENT_COLORS = {seg_id: cfg["color"] for seg_id, cfg in SEGMENT_CONFIG.items()}
SEGMENT_NAMES = {seg_id: cfg["name"] for seg_id, cfg in SEGMENT_CONFIG.items()}

# Priority order for display (rank 1 = highest priority)
SEGMENT_PRIORITY_ORDER = sorted(
    SEGMENT_CONFIG.keys(),
    key=lambda x: (SEGMENT_CONFIG[x]["priority_rank"], -x)
)

# Metric tooltips for UI
METRIC_TOOLTIPS = {
    "recent_12m_revenue": (
        "Revenue from orders placed in the 12 months before Oct 2024 snapshot. "
        "May be £0 for customers who haven't ordered in over a year."
    ),
    "recency_days": (
        "Days since last order (from Oct 2024 snapshot). "
        ">365 days = 'dormant' for active customer calculations."
    ),
    "estimates_per_year": (
        "Annualized rate of quote/estimate requests. "
        "High value with low conversion may indicate sales process friction."
    ),
    "avg_days_between_orders": (
        "Average gap between orders. Low value + short tenure may indicate "
        "onboarding burst followed by churn."
    ),
    "tenure_days": (
        "Days between first order and last order. "
        "Short tenure + high activity = burst pattern."
    ),
}


@st.cache_data(ttl=3600)
def load_cluster_profiles() -> dict:
    """Load cluster profiles with persona definitions"""
    profiles_path = MODELS_DIR / "cluster_profiles.json"

    if profiles_path.exists():
        with open(profiles_path, 'r') as f:
            return json.load(f)

    # Fallback profiles - 8 segments from hierarchical clustering
    # Segments 0-4: ADS core recluster (subclusters of initial mixed cluster 0)
    # Segments 5-7: Original primary clusters 1, 2, 3 (remapped)
    # CORRECTED based on boxplot validation and cluster analysis
    return {
        "0": {
            "name": "Early-Churn Burst",
            "description": "Short tenure (~59 days) but high activity burst (avg 8.5 days between orders, 20.6 estimates/year). These customers engaged intensively then churned - likely onboarding friction (spec/lead time/quality/MOQ issues).",
            "characteristics": {
                "monetary_range": "£10,614 avg",
                "frequency_range": "High burst activity",
                "tenure_range": "~59 days avg (short)",
                "estimates_per_year": "20.6 avg (high engagement)",
                "avg_days_between_orders": "8.5 days (frequent during active period)"
            },
            "recommended_actions": [
                "Automated friction-removal CTA",
                "Survey on onboarding experience",
                "Address spec/MOQ/lead time concerns",
                "Escalate only top-value subset for personal outreach"
            ],
            "risk_level": "MEDIUM - Onboarding Issue",
            "motion": "Friction Removal",
            "color": "#FF7043"
        },
        "1": {
            "name": "Lapsed Regular",
            "description": "Previously regular customers who stopped ordering. Need diagnosis before discounting - understand WHY they left before offering incentives.",
            "characteristics": {
                "monetary_range": "£6,166 avg",
                "frequency_range": "Regular historical pattern",
                "recency_range": "Dormant but recoverable"
            },
            "recommended_actions": [
                "Personal phone outreach - diagnosis first",
                "Avoid discount-first approach",
                "Understand service/quality/pricing concerns",
                "Tailored win-back based on feedback"
            ],
            "risk_level": "HIGH - Recoverable Value",
            "motion": "Diagnosis-First",
            "color": "#AB47BC"
        },
        "2": {
            "name": "Quote-Heavy Occasional",
            "description": "High estimates_per_year suggests frequent quoting but low conversion. This is a SALES PROCESS issue - they're interested but not converting. Focus on barrier removal and fast re-quoting.",
            "characteristics": {
                "monetary_range": "£6,347 avg",
                "frequency_range": "Occasional orders",
                "estimates_per_year": "High quote volume, low conversion"
            },
            "recommended_actions": [
                "Review quote-to-order conversion rate",
                "Fast re-quote with simplified process",
                "Remove barriers (MOQ, lead time, spec complexity)",
                "Sales process audit for this cohort"
            ],
            "risk_level": "HIGH - Sales Process Issue",
            "motion": "Conversion Win-back",
            "color": "#5C6BC0"
        },
        "3": {
            "name": "Project Re-quote",
            "description": "Higher AOV (£6,826) with infrequent, project-based ordering. These customers buy for specific projects - maintain awareness and re-engage when projects arise.",
            "characteristics": {
                "monetary_range": "£6,826 avg (higher AOV)",
                "frequency_range": "Infrequent, project-based",
                "recency_range": "Project cycle dependent"
            },
            "recommended_actions": [
                "Semi-personal quarterly outreach",
                "Project planning check-ins",
                "Case study and capability updates",
                "Be ready for fast turnaround when project starts"
            ],
            "risk_level": "MEDIUM - Project Cycle",
            "motion": "Project Re-quote",
            "color": "#26A69A"
        },
        "4": {
            "name": "Win-back VIP",
            "description": "CRITICAL: £91,587 avg revenue, 50% still have recent_12m engagement. £10.7M total opportunity. Executive-level tiered win-back with reason-coded churn analysis.",
            "characteristics": {
                "monetary_range": "£91,587 avg (median £19,748)",
                "frequency_range": "29.4 orders avg (high volume)",
                "recency_range": "576 days avg (50% have recent activity)",
                "recent_12m_revenue": "£6,584 avg (indicates some still active)"
            },
            "recommended_actions": [
                "URGENT: Executive outreach within 48 hours",
                "Tiered offer ladder: Service fix → Commercial terms → Incentive",
                "Reason-coded churn analysis for each account",
                "Account review meeting with senior leadership",
                "Premium return package with dedicated support"
            ],
            "risk_level": "CRITICAL - Highest Revenue at Risk",
            "motion": "Executive Win-back",
            "color": "#E53935"
        },
        "5": {
            "name": "Active Regulars",
            "description": "TRUE REGULARS: Low recency, high tenure, high product diversity. These are your best active relationships - PROTECT and grow, don't treat as dormant.",
            "characteristics": {
                "monetary_range": "£3,856 avg",
                "frequency_range": "Regular ordering",
                "recency_range": "LOW recency (recent orders)",
                "tenure_days": "HIGH tenure (long relationship)",
                "product_diversity": "High (engaged across product lines)"
            },
            "recommended_actions": [
                "PROTECT: Dedicated account management",
                "Cross-sell and upsell opportunities",
                "Loyalty recognition program",
                "Quarterly business reviews",
                "Early access to new products"
            ],
            "risk_level": "PROTECT - Core Revenue",
            "motion": "Retention + Grow",
            "color": "#43A047"
        },
        "6": {
            "name": "Dormant Mid-Tenure",
            "description": "Had relationship (mid-tenure) but now 84% dormant. Worth moderate re-engagement effort with special return offers.",
            "characteristics": {
                "monetary_range": "£5,077 avg",
                "frequency_range": "2.7 orders avg",
                "recency_range": "1,018 days avg (84% dormant)"
            },
            "recommended_actions": [
                "'We miss you' email sequence",
                "Special return customer offer",
                "Quarterly touchpoints",
                "Re-engagement campaign"
            ],
            "risk_level": "LOW-MEDIUM",
            "motion": "Re-engagement",
            "color": "#FFA726"
        },
        "7": {
            "name": "Archive/Low-Touch",
            "description": "Long-cycle, low-value (£1,393 avg), near-zero recent_12m_revenue. True dormant/archive segment - minimal marketing investment only.",
            "characteristics": {
                "monetary_range": "£1,393 avg (LOWEST)",
                "frequency_range": "2.0 orders avg",
                "recency_range": "Very high (90% dormant)",
                "recent_12m_revenue": "Near zero"
            },
            "recommended_actions": [
                "Include in batch emails only (2x/year)",
                "No personal outreach - not cost-effective",
                "Consider for archive/write-off",
                "Seasonal promotional inclusion only"
            ],
            "risk_level": "LOWEST",
            "motion": "Batch Only",
            "color": "#78909C"
        }
    }


@st.cache_data(ttl=3600)
def load_company_data() -> pd.DataFrame:
    """Load the main company features dataset"""
    data_path = DATA_DIR / "company_features_processed_base.csv"

    if data_path.exists():
        df = pd.read_csv(data_path)
        return df

    st.error(f"Company data not found at {data_path}")
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_cluster_assignments() -> pd.DataFrame:
    """Load cluster assignments for all companies - using 8-segment hierarchical model"""
    # Use final_cluster_assignments.csv which has 8 segments from hierarchical clustering
    assignments_path = DATA_DIR / "ads_clustering" / "final_cluster_assignments.csv"

    if assignments_path.exists():
        df = pd.read_csv(assignments_path)
        # Rename to match expected column name
        if 'final_cluster' in df.columns:
            df = df.rename(columns={'final_cluster': 'ads_cluster'})
        return df

    # Fallback to old 4-cluster file
    old_path = DATA_DIR / "ads_clustering" / "ads_cluster_assignments.csv"
    if old_path.exists():
        return pd.read_csv(old_path)

    st.error("Cluster assignments not found")
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_cluster_profiles_detailed() -> pd.DataFrame:
    """Load detailed cluster statistics"""
    profiles_path = OUTPUTS_DIR / "cluster_profiles_detailed.csv"

    if profiles_path.exists():
        return pd.read_csv(profiles_path, index_col=0, header=[0, 1])

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_companies_by_segment(segment_id: int) -> pd.DataFrame:
    """Get all companies belonging to a specific segment"""
    companies = load_company_data()
    assignments = load_cluster_assignments()

    if companies.empty or assignments.empty:
        return pd.DataFrame()

    # Merge companies with their cluster assignments
    merged = companies.merge(assignments, on='company', how='left')

    # Filter by segment
    segment_companies = merged[merged['ads_cluster'] == segment_id]

    return segment_companies


@st.cache_data(ttl=3600)
def get_company_details(company_name: str) -> dict:
    """Get detailed information for a specific company"""
    companies = load_company_data()
    assignments = load_cluster_assignments()
    profiles = load_cluster_profiles()

    if companies.empty:
        return {}

    company_row = companies[companies['company'] == company_name]

    if company_row.empty:
        return {}

    company_data = company_row.iloc[0].to_dict()

    # Add cluster info
    if not assignments.empty:
        cluster_row = assignments[assignments['company'] == company_name]
        if not cluster_row.empty:
            cluster_id = str(cluster_row.iloc[0]['ads_cluster'])
            company_data['cluster_id'] = int(cluster_id)
            company_data['cluster_name'] = profiles.get(cluster_id, {}).get('name', 'Unknown')
            company_data['cluster_profile'] = profiles.get(cluster_id, {})

    return company_data


@st.cache_data(ttl=3600)
def get_feature_stats() -> dict:
    """Get statistics for key features across all segments"""
    companies = load_company_data()
    assignments = load_cluster_assignments()

    if companies.empty or assignments.empty:
        return {}

    merged = companies.merge(assignments, on='company', how='left')

    key_features = [
        'frequency', 'monetary_total', 'monetary_mean',
        'recency_days', 'tenure_days', 'estimates_per_year',
        'avg_days_between_orders', 'product_type_diversity'
    ]

    # Filter to existing columns
    available_features = [f for f in key_features if f in merged.columns]

    stats = {}
    for feature in available_features:
        stats[feature] = {
            'overall_mean': merged[feature].mean(),
            'overall_median': merged[feature].median(),
            'by_segment': merged.groupby('ads_cluster')[feature].agg(['mean', 'median', 'std']).to_dict()
        }

    return stats
