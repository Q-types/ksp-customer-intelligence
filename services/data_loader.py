"""
Data Loading Service
Handles loading and caching of all data files
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

# Centralized segment colors - single source of truth for all pages
# Based on QA audit: colors reflect priority/risk, not original assumptions
SEGMENT_COLORS = {
    0: "#9E9E9E",  # Grey - Dormant One-Timers (low priority)
    1: "#4CAF50",  # Green - Recently Active Small (nurture)
    2: "#9C27B0",  # Purple - Dormant Occasional
    3: "#673AB7",  # Deep Purple - Dormant Moderate
    4: "#F44336",  # Red - High-Value At-Risk (CRITICAL)
    5: "#607D8B",  # Blue-Grey - Long-Tenure Inactive
    6: "#FF9800",  # Orange - Dormant Mid-Tenure
    7: "#795548",  # Brown - Low-Value Dormant (lowest priority)
}


@st.cache_data(ttl=3600)
def load_cluster_profiles() -> dict:
    """Load cluster profiles with persona definitions"""
    profiles_path = MODELS_DIR / "cluster_profiles.json"

    if profiles_path.exists():
        with open(profiles_path, 'r') as f:
            return json.load(f)

    # Fallback profiles - 8 segments from hierarchical clustering
    # Segments 0-4: subclusters of original Cluster 0 (855 companies)
    # Segments 5-7: original primary clusters 1, 2, 3 (remapped)
    # CORRECTED based on QA audit - labels now match actual data metrics
    return {
        "0": {
            "name": "Dormant One-Timers",
            "description": "Single or few orders, long time ago. Low engagement history. Win-back unlikely to be cost-effective.",
            "characteristics": {
                "monetary_range": "£10,615 avg (median £1,621)",
                "frequency_range": "3.7 orders avg (median 1)",
                "recency_range": "1,420 days avg (88% dormant)"
            },
            "recommended_actions": [
                "Batch re-engagement email only",
                "Remove from active marketing lists",
                "Consider for seasonal promotions only"
            ],
            "risk_level": "Low Priority",
            "color": "#9E9E9E"
        },
        "1": {
            "name": "Recently Active Small",
            "description": "Small segment with some recent activity (57% active). Nurture and develop potential.",
            "characteristics": {
                "monetary_range": "£6,166 avg",
                "frequency_range": "2.7 orders avg",
                "recency_range": "716 days avg (43% dormant)"
            },
            "recommended_actions": [
                "Monthly touchpoint emails",
                "Product education content",
                "Second purchase incentive"
            ],
            "risk_level": "Nurture",
            "color": "#4CAF50"
        },
        "2": {
            "name": "Dormant Occasional",
            "description": "Project-based historical buyers, now inactive. Maintain awareness for next project.",
            "characteristics": {
                "monetary_range": "£6,347 avg",
                "frequency_range": "2.7 orders avg",
                "recency_range": "1,190 days avg (84% dormant)"
            },
            "recommended_actions": [
                "Quarterly capability updates",
                "Project inquiry prompts",
                "Case study sharing"
            ],
            "risk_level": "Low-Medium",
            "color": "#9C27B0"
        },
        "3": {
            "name": "Dormant Moderate",
            "description": "Some order history but now inactive. Content-led nurture back slowly.",
            "characteristics": {
                "monetary_range": "£6,826 avg",
                "frequency_range": "2.8 orders avg",
                "recency_range": "1,288 days avg (86% dormant)"
            },
            "recommended_actions": [
                "Re-engagement email sequence",
                "Industry news sharing",
                "Product update announcements"
            ],
            "risk_level": "Medium",
            "color": "#673AB7"
        },
        "4": {
            "name": "High-Value At-Risk",
            "description": "TOP PRIORITY: £92K avg revenue, 50% still engaging. Executive recovery program for £10.7M opportunity.",
            "characteristics": {
                "monetary_range": "£91,587 avg (median £19,748)",
                "frequency_range": "29.4 orders avg (median 10)",
                "recency_range": "576 days avg (50% dormant)"
            },
            "recommended_actions": [
                "Executive outreach within 48 hours",
                "Account review meeting request",
                "Premium return incentive"
            ],
            "risk_level": "CRITICAL",
            "color": "#F44336"
        },
        "5": {
            "name": "Long-Tenure Inactive",
            "description": "Old customers (1,722 day tenure) with minimal recent engagement. Light-touch re-engagement.",
            "characteristics": {
                "monetary_range": "£3,856 avg",
                "frequency_range": "2.0 orders avg",
                "recency_range": "449 days avg (60% dormant)"
            },
            "recommended_actions": [
                "Quarterly check-in email",
                "Capability reminder",
                "Low-cost re-engagement"
            ],
            "risk_level": "Low",
            "color": "#607D8B"
        },
        "6": {
            "name": "Dormant Mid-Tenure",
            "description": "Had relationship but 84% now dormant. Re-engagement targets with special return offers.",
            "characteristics": {
                "monetary_range": "£5,077 avg",
                "frequency_range": "2.7 orders avg",
                "recency_range": "1,018 days avg (84% dormant)"
            },
            "recommended_actions": [
                "'We miss you' email sequence",
                "Special return customer offer",
                "Quarterly touchpoints"
            ],
            "risk_level": "Medium",
            "color": "#FF9800"
        },
        "7": {
            "name": "Low-Value Dormant",
            "description": "Lowest value segment (£1,393 avg), highest dormancy (90%). Minimal marketing investment.",
            "characteristics": {
                "monetary_range": "£1,393 avg (LOWEST)",
                "frequency_range": "2.0 orders avg",
                "recency_range": "905 days avg (90% dormant)"
            },
            "recommended_actions": [
                "Include in batch emails only",
                "No personal outreach",
                "Consider for write-off"
            ],
            "risk_level": "Very Low",
            "color": "#795548"
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
