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


@st.cache_data(ttl=3600)
def load_cluster_profiles() -> dict:
    """Load cluster profiles with persona definitions"""
    profiles_path = MODELS_DIR / "cluster_profiles.json"

    if profiles_path.exists():
        with open(profiles_path, 'r') as f:
            return json.load(f)

    # Fallback profiles - 8 segments from hierarchical clustering
    # Segments 0-4: subclusters of original dormant cluster
    # Segments 5-7: original active clusters (remapped)
    return {
        "0": {
            "name": "Dormant One-Timers",
            "description": "Single or few orders, long time ago. Low engagement history. Win-back unlikely to be cost-effective.",
            "characteristics": {
                "monetary_range": "Low (single order value)",
                "frequency_range": "1 order only",
                "recency_range": ">2 years since last order"
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
            "name": "Lapsed Regulars",
            "description": "Previously regular customers who stopped ordering. BEST win-back candidates - they know the product.",
            "characteristics": {
                "monetary_range": "Previously moderate-high",
                "frequency_range": "Multiple past orders",
                "recency_range": ">1 year dormant"
            },
            "recommended_actions": [
                "Personal outreach call",
                "Special return customer offer",
                "Survey to understand why they left"
            ],
            "risk_level": "Win-Back Priority",
            "color": "#E91E63"
        },
        "2": {
            "name": "Occasional Past",
            "description": "Infrequent past customers. Likely project-based needs.",
            "characteristics": {
                "monetary_range": "Variable per project",
                "frequency_range": "2-3 orders historically",
                "recency_range": ">1 year"
            },
            "recommended_actions": [
                "Quarterly check-in email",
                "Project inquiry follow-up",
                "Catalogue/capability updates"
            ],
            "risk_level": "Medium",
            "color": "#9C27B0"
        },
        "3": {
            "name": "Moderate History",
            "description": "Some order history but now inactive. Potential for reactivation with right offer.",
            "characteristics": {
                "monetary_range": "Mid-range historically",
                "frequency_range": "Several past orders",
                "recency_range": ">1 year"
            },
            "recommended_actions": [
                "Re-engagement email sequence",
                "Product update announcements",
                "Industry news sharing"
            ],
            "risk_level": "Medium",
            "color": "#673AB7"
        },
        "4": {
            "name": "High-Value Dormant",
            "description": "Previously HIGH VALUE customers now inactive. TOP WIN-BACK PRIORITY - significant revenue recovery potential.",
            "characteristics": {
                "monetary_range": "High (>£10,000 historical)",
                "frequency_range": "Multiple past orders",
                "recency_range": ">1 year dormant"
            },
            "recommended_actions": [
                "Executive/senior outreach",
                "Premium return incentive",
                "Account review meeting request"
            ],
            "risk_level": "Critical - High Value",
            "color": "#C62828"
        },
        "5": {
            "name": "New Prospects",
            "description": "Recently acquired customers with limited order history. Potential for development.",
            "characteristics": {
                "monetary_range": "Low-moderate (early stage)",
                "frequency_range": "1-2 orders",
                "recency_range": "Recent activity"
            },
            "recommended_actions": [
                "Welcome onboarding sequence",
                "Introductory consultation offer",
                "Product range showcase"
            ],
            "risk_level": "Nurture",
            "color": "#00BCD4"
        },
        "6": {
            "name": "Growth Potential",
            "description": "Active customers showing growth trajectory. Expansion opportunity.",
            "characteristics": {
                "monetary_range": "Mid-range (£5,000-£20,000)",
                "frequency_range": "Regular ordering",
                "recency_range": "Active (<6 months)"
            },
            "recommended_actions": [
                "Business development call",
                "Cross-sell campaign",
                "Product range expansion"
            ],
            "risk_level": "Opportunity",
            "color": "#1976D2"
        },
        "7": {
            "name": "High-Value Regulars",
            "description": "Premium customers - your best accounts. PROTECT these relationships.",
            "characteristics": {
                "monetary_range": "Top tier (>£20,000)",
                "frequency_range": "Frequent orders (10+)",
                "recency_range": "Active (<3 months)"
            },
            "recommended_actions": [
                "Dedicated account manager",
                "Loyalty rewards program",
                "Priority service and new product access"
            ],
            "risk_level": "Protect",
            "color": "#2E7D32"
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
