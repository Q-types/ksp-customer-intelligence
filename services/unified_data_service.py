"""
Unified Data Service
Combines customer segmentation, prospect scoring, and actionable insights
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

# Base paths - using local data within dashboard for standalone deployment
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COMPANIES_DIR = DATA_DIR / "companies"
PROSPECTS_DIR = DATA_DIR / "prospects"
MODELS_DIR = BASE_DIR / "models"

# DATA SNAPSHOT DATE - all recency/activity metrics are relative to this date
# The underlying order data is from KSP's system up to October 2024
DATA_SNAPSHOT_DATE = datetime(2024, 10, 18)
DATA_SNAPSHOT_STR = "October 2024"


# =============================================================================
# CORE DATA LOADERS
# =============================================================================

def get_data_snapshot_info() -> Dict:
    """Return data snapshot information for display"""
    return {
        'date': DATA_SNAPSHOT_DATE,
        'date_str': DATA_SNAPSHOT_STR,
        'warning': f"Data as of {DATA_SNAPSHOT_STR}. Recency metrics (e.g., 'days since last order') are relative to this date, not today."
    }


@st.cache_data(ttl=3600)
def load_customer_data() -> pd.DataFrame:
    """Load and merge customer features with final cluster assignments (8 segments)"""
    features_path = COMPANIES_DIR / "company_features_processed_base.csv"
    # Use final clustering with subclusters
    clusters_path = COMPANIES_DIR / "ads_clustering" / "final_cluster_assignments.csv"

    if not features_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(features_path)

    if clusters_path.exists():
        clusters = pd.read_csv(clusters_path)
        df = df.merge(clusters, on='company', how='left')
        # Rename to consistent column name
        if 'final_cluster' in df.columns:
            df['ads_cluster'] = df['final_cluster']
            df.drop(columns=['final_cluster'], inplace=True)

    return df


@st.cache_data(ttl=3600)
def load_prospect_data() -> pd.DataFrame:
    """Load scored prospects with packaging fit"""
    prospects_path = PROSPECTS_DIR / "scored_prospects_with_packaging.csv"

    if prospects_path.exists():
        return pd.read_csv(prospects_path)

    # Try alternative path
    alt_path = PROSPECTS_DIR / "scored_prospects.csv"
    if alt_path.exists():
        return pd.read_csv(alt_path)

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_segment_profiles() -> Dict:
    """Load segment profile definitions - 8 segments from hierarchical clustering"""
    return {
        # Subclusters of original dormant customers (0-4)
        0: {
            "name": "Dormant One-Timers",
            "description": "Single/few orders, long time ago. Low engagement history. Win-back unlikely.",
            "color": "#9E9E9E",
            "risk_level": "Low Priority",
            "icon": "⚪",
            "actions": ["Batch re-engagement email", "Remove from active lists", "Seasonal promotion only"]
        },
        1: {
            "name": "Lapsed Regulars",
            "description": "Previously regular customers who stopped. Best win-back candidates.",
            "color": "#E91E63",
            "risk_level": "Win-Back Priority",
            "icon": "💔",
            "actions": ["Personal outreach call", "Special return offer", "Survey for feedback"]
        },
        2: {
            "name": "Occasional Past",
            "description": "Infrequent past customers. Project-based needs.",
            "color": "#9C27B0",
            "risk_level": "Medium",
            "icon": "🔮",
            "actions": ["Quarterly check-in", "Project inquiry", "Catalogue update"]
        },
        3: {
            "name": "Moderate History",
            "description": "Some order history but inactive. Potential for reactivation.",
            "color": "#673AB7",
            "risk_level": "Medium",
            "icon": "📊",
            "actions": ["Re-engagement sequence", "Product update email", "Industry news sharing"]
        },
        4: {
            "name": "High-Value Dormant",
            "description": "Previously high-value customers now inactive. TOP WIN-BACK PRIORITY.",
            "color": "#C62828",
            "risk_level": "Critical - High Value",
            "icon": "🔴",
            "actions": ["Executive outreach", "Premium return incentive", "Account review meeting"]
        },
        # Original clusters 1, 2, 3 mapped to 5, 6, 7
        5: {
            "name": "New Prospects",
            "description": "Recently acquired customers. Onboarding and relationship building.",
            "color": "#00BCD4",
            "risk_level": "Nurture",
            "icon": "🆕",
            "actions": ["Welcome sequence", "Intro consultation", "Product showcase"]
        },
        6: {
            "name": "Growth Potential",
            "description": "Active customers with expansion opportunity. GROW these accounts.",
            "color": "#1976D2",
            "risk_level": "Opportunity",
            "icon": "📈",
            "actions": ["Business development call", "Cross-sell campaign", "Range expansion"]
        },
        7: {
            "name": "High-Value Regulars",
            "description": "Premium active customers. PROTECT and nurture these VIPs.",
            "color": "#2E7D32",
            "risk_level": "Protect",
            "icon": "⭐",
            "actions": ["Dedicated account manager", "Loyalty rewards", "Priority service"]
        }
    }


# =============================================================================
# PRIORITY & ACTION CALCULATIONS
# =============================================================================

def calculate_churn_risk(row: pd.Series) -> float:
    """Calculate churn risk score (0-100) based on segment from hierarchical clustering"""
    segment = row.get('ads_cluster', 0)
    recency = row.get('recency_days', 0)
    frequency = row.get('frequency', 1)

    # 8-segment risk mapping from hierarchical clustering
    # Segments 0-4: subclusters of original dormant cluster (high risk)
    # Segments 5-7: original clusters 1-3 (active customers)
    segment_base_risk = {
        0: 90,   # Dormant One-Timers - highest risk, low value
        1: 75,   # Lapsed Regulars - win-back priority
        2: 70,   # Occasional Past - moderate risk
        3: 65,   # Moderate History - some risk
        4: 85,   # High-Value Dormant - critical win-back
        5: 30,   # New Prospects - nurture phase
        6: 25,   # Growth Potential - active, low risk
        7: 15,   # High-Value Regulars - protect, lowest risk
    }.get(int(segment) if pd.notna(segment) else 0, 50)

    # Minor recency adjustment
    if recency <= 365:
        recency_adj = -10
    elif recency <= 730:
        recency_adj = 0
    else:
        recency_adj = 5

    # Frequency adjustment
    if frequency >= 5:
        freq_adj = -5
    else:
        freq_adj = 0

    risk = segment_base_risk + recency_adj + freq_adj
    return min(100, max(0, risk))


def calculate_revenue_at_stake(row: pd.Series) -> float:
    """Estimate annual revenue at risk if customer churns"""
    monetary_total = row.get('monetary_total', 0)
    tenure_days = row.get('tenure_days', 365)

    if tenure_days <= 0:
        return 0

    # Annualized revenue
    annual_revenue = (monetary_total / tenure_days) * 365

    # Risk-weighted
    churn_risk = row.get('churn_risk', 50) / 100
    return annual_revenue * churn_risk


def calculate_expansion_potential(row: pd.Series, segment_avg: Dict) -> float:
    """Calculate potential revenue uplift based on segment comparison"""
    segment = row.get('ads_cluster', 2)
    current_revenue = row.get('monetary_total', 0)

    # Compare to segment average
    segment_avg_revenue = segment_avg.get(segment, current_revenue)

    if current_revenue >= segment_avg_revenue:
        return 0

    return segment_avg_revenue - current_revenue


@st.cache_data(ttl=3600)
def get_daily_priorities() -> Dict:
    """Get prioritized daily action items"""
    customers = load_customer_data().copy()
    prospects = load_prospect_data()

    if customers.empty:
        return {"at_risk": [], "hot_prospects": [], "expansion": [], "metrics": {}}

    # Calculate churn risk for all customers
    customers['churn_risk'] = customers.apply(calculate_churn_risk, axis=1)
    customers['revenue_at_stake'] = customers.apply(calculate_revenue_at_stake, axis=1)

    # Segment averages for expansion calculation
    segment_avg = customers.groupby('ads_cluster')['monetary_total'].mean().to_dict()
    customers['expansion_potential'] = customers.apply(
        lambda r: calculate_expansion_potential(r, segment_avg), axis=1
    )

    # WIN-BACK TARGETS: High-value dormant customers worth recovering
    # Focus on segments 1 (Lapsed Regulars) and 4 (High-Value Dormant) - best win-back candidates
    winback_candidates = customers[
        customers['ads_cluster'].isin([1, 4])  # Best win-back segments
    ].copy()
    if not winback_candidates.empty:
        winback_candidates['winback_score'] = (
            winback_candidates['monetary_total'] / winback_candidates['monetary_total'].max() * 60 +
            winback_candidates['frequency'] / winback_candidates['frequency'].max() * 40
        )
        at_risk = winback_candidates.nlargest(10, 'winback_score')[[
            'company', 'ads_cluster', 'recency_days', 'frequency',
            'monetary_total', 'churn_risk', 'revenue_at_stake'
        ]].to_dict('records')
    else:
        at_risk = []

    # HOT PROSPECTS (high ICP score, packaging fit)
    hot_prospects = []
    if not prospects.empty and 'prospect_score' in prospects.columns:
        hot_prospects = prospects[
            (prospects['priority_tier'] == 'Hot') |
            (prospects['prospect_score'] >= 80)
        ].nlargest(10, 'prospect_score')[[
            'company_name', 'industry_sector', 'prospect_score',
            'priority_tier', 'packaging_need', 'region'
        ]].to_dict('records')

    # EXPANSION OPPORTUNITIES: Active customers who could buy more
    # Segments 5, 6, 7 are the active ones (New Prospects, Growth Potential, High-Value Regulars)
    expansion_candidates = customers[
        customers['ads_cluster'].isin([5, 6, 7])  # Active segments
    ].copy()
    if not expansion_candidates.empty:
        # Score by frequency potential and recent activity
        expansion_candidates['expansion_score'] = (
            expansion_candidates['monetary_total'] +
            (365 - expansion_candidates['recency_days'].clip(upper=365)) * 10
        )
        expansion = expansion_candidates.nlargest(10, 'expansion_score')[[
            'company', 'ads_cluster', 'monetary_total', 'frequency', 'expansion_potential'
        ]].to_dict('records')
    else:
        expansion = []

    # METRICS - 8-segment model
    # Active: 5 (New Prospects), 6 (Growth Potential), 7 (High-Value Regulars)
    # Win-back priority: 1 (Lapsed Regulars), 4 (High-Value Dormant)
    # Low priority dormant: 0 (One-Timers), 2 (Occasional), 3 (Moderate History)
    active_customers = customers[customers['ads_cluster'].isin([5, 6, 7])]
    winback_priority = customers[customers['ads_cluster'].isin([1, 4])]
    low_priority_dormant = customers[customers['ads_cluster'].isin([0, 2, 3])]

    metrics = {
        'total_customers': len(customers),
        'active_customers': len(active_customers),
        'winback_priority': len(winback_priority),
        'low_priority_dormant': len(low_priority_dormant),
        'high_value_count': len(customers[customers['ads_cluster'] == 7]),
        'growth_potential_count': len(customers[customers['ads_cluster'] == 6]),
        'new_prospects_count': len(customers[customers['ads_cluster'] == 5]),
        'winback_candidates': len(winback_priority),
        'at_risk_revenue': winback_priority['monetary_total'].sum(),
        'hot_prospects_count': len(hot_prospects),
        'expansion_potential': active_customers['monetary_total'].sum() * 0.2
    }

    return {
        "at_risk": at_risk,
        "hot_prospects": hot_prospects,
        "expansion": expansion,
        "metrics": metrics
    }


# =============================================================================
# REVENUE OPPORTUNITIES
# =============================================================================

@st.cache_data(ttl=3600)
def get_revenue_leakage() -> pd.DataFrame:
    """Get at-risk revenue with win-back suggestions"""
    customers = load_customer_data()
    profiles = load_segment_profiles()

    if customers.empty:
        return pd.DataFrame()

    customers['churn_risk'] = customers.apply(calculate_churn_risk, axis=1)
    customers['revenue_at_stake'] = customers.apply(calculate_revenue_at_stake, axis=1)

    # Filter to at-risk customers
    at_risk = customers[customers['churn_risk'] >= 50].copy()

    # Add segment info
    at_risk['segment_name'] = at_risk['ads_cluster'].map(
        lambda x: profiles.get(x, {}).get('name', f'Segment {x}')
    )

    # Win-back suggestions based on segment
    def get_suggestion(row):
        segment = row['ads_cluster']
        recency = row['recency_days']

        if segment == 0:  # At-Risk Dormant
            return "Win-back: Special return offer + personal call"
        elif recency > 180:
            return "Re-engagement: Check-in call + project inquiry"
        elif row['frequency'] >= 5:
            return "Retention: Schedule account review"
        else:
            return "Nurture: Add to reactivation email sequence"

    at_risk['suggestion'] = at_risk.apply(get_suggestion, axis=1)

    return at_risk[[
        'company', 'segment_name', 'recency_days', 'frequency',
        'monetary_total', 'churn_risk', 'revenue_at_stake', 'suggestion'
    ]].sort_values('revenue_at_stake', ascending=False)


@st.cache_data(ttl=3600)
def get_expansion_opportunities() -> pd.DataFrame:
    """Get customers with cross-sell/upsell potential"""
    customers = load_customer_data()
    profiles = load_segment_profiles()

    if customers.empty:
        return pd.DataFrame()

    # Product type columns
    ptype_cols = [c for c in customers.columns if c.startswith('ptype_')]

    # Calculate segment averages
    segment_stats = customers.groupby('ads_cluster').agg({
        'monetary_total': 'mean',
        'frequency': 'mean',
        'orders_per_year': 'mean' if 'orders_per_year' in customers.columns else 'monetary_total'
    }).to_dict('index')

    # Find underperforming customers in good segments
    opportunities = []
    for _, row in customers.iterrows():
        segment = row.get('ads_cluster', 6)
        if segment not in [6, 7]:  # Only Growth Potential (6) and High-Value Regulars (7)
            continue

        seg_avg = segment_stats.get(segment, {})
        current_revenue = row.get('monetary_total', 0)
        segment_avg_revenue = seg_avg.get('monetary_total', current_revenue)

        if current_revenue < segment_avg_revenue * 0.7:  # Below 70% of segment avg
            # Find underutilized product types
            current_ptypes = [c.replace('ptype_', '').replace('_pct', '')
                            for c in ptype_cols if row.get(c, 0) > 0.1]

            opportunities.append({
                'company': row['company'],
                'segment_name': profiles.get(segment, {}).get('name', f'Segment {segment}'),
                'current_revenue': current_revenue,
                'segment_avg': segment_avg_revenue,
                'potential_uplift': segment_avg_revenue - current_revenue,
                'current_products': ', '.join(current_ptypes[:3]) if current_ptypes else 'Various',
                'suggestion': f"Explore additional product types - peer average is £{segment_avg_revenue:,.0f}"
            })

    return pd.DataFrame(opportunities).sort_values('potential_uplift', ascending=False).head(20)


@st.cache_data(ttl=3600)
def get_market_gaps() -> pd.DataFrame:
    """Identify underrepresented industries/regions"""
    prospects = load_prospect_data()

    if prospects.empty:
        return pd.DataFrame()

    # Industry gaps - high-potential industries we're not serving well
    industry_summary = prospects.groupby('industry_sector').agg({
        'prospect_score': ['mean', 'count'],
        'packaging_need': lambda x: (x == 'HIGH').sum()
    }).reset_index()
    industry_summary.columns = ['industry', 'avg_score', 'prospect_count', 'high_need_count']

    # Find high-potential gaps
    industry_summary['opportunity_score'] = (
        industry_summary['avg_score'] *
        (industry_summary['high_need_count'] / industry_summary['prospect_count'].replace(0, 1))
    )

    gaps = industry_summary.nlargest(10, 'opportunity_score')
    gaps['suggestion'] = gaps.apply(
        lambda r: f"Target {r['high_need_count']} high-need prospects in {r['industry']}", axis=1
    )

    return gaps


# =============================================================================
# PROSPECT PIPELINE
# =============================================================================

@st.cache_data(ttl=3600)
def get_prospect_pipeline() -> Dict:
    """Get prospect funnel data"""
    prospects = load_prospect_data()

    if prospects.empty:
        return {"funnel": {}, "by_industry": {}, "by_region": {}, "prospects": pd.DataFrame()}

    # Funnel by tier
    tier_order = ['Hot', 'Warm', 'Cool', 'Cold']
    funnel = {}
    for tier in tier_order:
        tier_prospects = prospects[prospects['priority_tier'] == tier]
        funnel[tier] = {
            'count': len(tier_prospects),
            'avg_score': tier_prospects['prospect_score'].mean() if len(tier_prospects) > 0 else 0,
            'high_need_pct': (tier_prospects['packaging_need'] == 'HIGH').mean() * 100 if len(tier_prospects) > 0 else 0
        }

    # By industry
    by_industry = prospects.groupby('industry_sector').agg({
        'company_name': 'count',
        'prospect_score': 'mean',
        'packaging_need': lambda x: (x == 'HIGH').sum()
    }).reset_index()
    by_industry.columns = ['industry', 'count', 'avg_score', 'high_need']

    # By region
    by_region = prospects.groupby('region').agg({
        'company_name': 'count',
        'prospect_score': 'mean'
    }).reset_index()
    by_region.columns = ['region', 'count', 'avg_score']

    return {
        "funnel": funnel,
        "by_industry": by_industry.to_dict('records'),
        "by_region": by_region.to_dict('records'),
        "prospects": prospects
    }


@st.cache_data(ttl=3600)
def get_best_fit_prospects(limit: int = 20) -> pd.DataFrame:
    """Get prospects most similar to best customers"""
    prospects = load_prospect_data()
    customers = load_customer_data()

    if prospects.empty:
        return pd.DataFrame()

    # Get characteristics of High-Value Regulars (segment 7)
    if not customers.empty and 'ads_cluster' in customers.columns:
        champions = customers[customers['ads_cluster'] == 7]
        if len(champions) > 0:
            # Champion industries (simplified)
            pass

    # Filter to best prospects
    best = prospects[
        (prospects['prospect_score'] >= 75) &
        (prospects['packaging_need'] == 'HIGH')
    ].nlargest(limit, 'prospect_score')

    return best[[
        'company_name', 'industry_sector', 'region',
        'prospect_score', 'priority_tier', 'packaging_need',
        'industry_score', 'age_score', 'size_score'
    ]]


# =============================================================================
# CUSTOMER EXPLORER
# =============================================================================

@st.cache_data(ttl=3600)
def get_customer_360(company_name: str) -> Dict:
    """Get complete customer profile"""
    customers = load_customer_data()
    profiles = load_segment_profiles()

    if customers.empty:
        return {}

    customer = customers[customers['company'] == company_name]

    if customer.empty:
        return {}

    row = customer.iloc[0]
    segment_id = int(row.get('ads_cluster', 2))
    profile = profiles.get(segment_id, {})

    # Calculate metrics
    churn_risk = calculate_churn_risk(row)

    # Lifetime value estimate (3-year projection)
    annual_revenue = row.get('monetary_total', 0) / max(row.get('tenure_days', 365), 1) * 365
    retention_rate = max(0.5, 1 - (churn_risk / 100))
    ltv = sum([annual_revenue * (retention_rate ** year) for year in range(3)])

    return {
        'company': company_name,
        'segment_id': segment_id,
        'segment_name': profile.get('name', 'Unknown'),
        'segment_color': profile.get('color', '#666'),
        'risk_level': profile.get('risk_level', 'Unknown'),

        # Financial metrics
        'total_revenue': row.get('monetary_total', 0),
        'avg_order_value': row.get('monetary_mean', 0),
        'order_count': row.get('frequency', 0),
        'lifetime_value': ltv,

        # Engagement metrics
        'recency_days': row.get('recency_days', 0),
        'tenure_days': row.get('tenure_days', 0),
        'avg_days_between_orders': row.get('avg_days_between_orders', 0),
        'orders_per_year': row.get('orders_per_year', 0),

        # Risk metrics
        'churn_risk': churn_risk,
        'revenue_at_stake': calculate_revenue_at_stake(row.to_dict() | {'churn_risk': churn_risk}),

        # Product mix
        'avg_quantity': row.get('avg_quantity', 0),
        'avg_margin': row.get('avg_margin', 0),

        # Recommended actions
        'recommended_actions': profile.get('actions', [])
    }


@st.cache_data(ttl=3600)
def search_customers(query: str = "", segment: Optional[int] = None,
                     sort_by: str = 'monetary_total', limit: int = 50) -> pd.DataFrame:
    """Search and filter customers"""
    customers = load_customer_data()
    profiles = load_segment_profiles()

    if customers.empty:
        return pd.DataFrame()

    # Calculate churn risk
    customers['churn_risk'] = customers.apply(calculate_churn_risk, axis=1)

    # Filter by query
    if query:
        customers = customers[customers['company'].str.contains(query, case=False, na=False)]

    # Filter by segment
    if segment is not None:
        customers = customers[customers['ads_cluster'] == segment]

    # Add segment name
    customers['segment_name'] = customers['ads_cluster'].map(
        lambda x: profiles.get(int(x) if pd.notna(x) else 2, {}).get('name', 'Unknown')
    )

    # Sort
    if sort_by in customers.columns:
        ascending = sort_by == 'recency_days'  # Lower recency is better
        customers = customers.sort_values(sort_by, ascending=ascending)

    # Select columns
    display_cols = ['company', 'segment_name', 'monetary_total', 'frequency',
                    'recency_days', 'churn_risk']
    available_cols = [c for c in display_cols if c in customers.columns]

    return customers[available_cols].head(limit)


# =============================================================================
# SEGMENT SUMMARY
# =============================================================================

@st.cache_data(ttl=3600)
def get_segment_summary() -> pd.DataFrame:
    """Get summary of all segments"""
    customers = load_customer_data()
    profiles = load_segment_profiles()

    if customers.empty or 'ads_cluster' not in customers.columns:
        return pd.DataFrame()

    summary = []
    for seg_id in sorted(customers['ads_cluster'].dropna().unique()):
        seg_id = int(seg_id)
        seg_data = customers[customers['ads_cluster'] == seg_id]
        profile = profiles.get(seg_id, {})

        summary.append({
            'segment_id': seg_id,
            'name': profile.get('name', f'Segment {seg_id}'),
            'icon': profile.get('icon', ''),
            'color': profile.get('color', '#666'),
            'count': len(seg_data),
            'pct': len(seg_data) / len(customers) * 100,
            'total_revenue': seg_data['monetary_total'].sum() if 'monetary_total' in seg_data else 0,
            'avg_revenue': seg_data['monetary_total'].mean() if 'monetary_total' in seg_data else 0,
            'avg_frequency': seg_data['frequency'].mean() if 'frequency' in seg_data else 0,
            'avg_recency': seg_data['recency_days'].mean() if 'recency_days' in seg_data else 0,
            'risk_level': profile.get('risk_level', 'Unknown')
        })

    return pd.DataFrame(summary)
