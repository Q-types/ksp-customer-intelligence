"""
KSP Customer Intelligence Command Center
Unified dashboard combining customer analytics, prospect pipeline, and revenue opportunities
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (local development)
# For Streamlit Cloud, use secrets.toml instead
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory as fallback
    env_path_parent = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path_parent)

import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="KSP Intelligence Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.unified_data_service import (
    get_daily_priorities,
    get_segment_summary,
    get_prospect_pipeline,
    load_segment_profiles,
    get_data_snapshot_info
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }

    /* Priority cards */
    .priority-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.25rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .priority-card h3 {
        font-size: 2rem;
        margin: 0;
        font-weight: 700;
    }
    .priority-card p {
        margin: 0.25rem 0 0 0;
        opacity: 0.9;
        font-size: 0.85rem;
    }

    /* Alert cards */
    .alert-card {
        border-left: 4px solid #C62828;
        background: #FFF5F5;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.75rem;
        color: #1a1a1a !important;
    }
    .alert-card strong {
        color: #000000 !important;
        font-size: 1rem;
    }
    .alert-card small {
        color: #333333 !important;
        line-height: 1.4;
    }
    .alert-card.warning {
        border-left-color: #F57C00;
        background: #FFF8E1;
    }
    .alert-card.success {
        border-left-color: #2E7D32;
        background: #E8F5E9;
    }

    /* Action button styling */
    .action-row {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    /* Segment pills */
    .segment-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
    }

    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }

    /* Navigation tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

with st.sidebar:
    st.markdown("## 📦 KSP Intelligence")
    st.markdown("---")

    page = st.radio(
        "Select View",
        ["🎯 Action Center", "💰 Revenue Opportunities", "🔍 Prospect Pipeline", "📊 Customer Explorer", "🔎 Company Search", "📧 Marketing Playbook"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick stats
    priorities = get_daily_priorities()
    metrics = priorities.get('metrics', {})

    st.markdown("### Quick Stats")
    st.metric("Active Customers", f"{metrics.get('active_customers', 0):,}")
    st.metric("Win-Back Targets", f"{metrics.get('winback_candidates', 0):,}")
    st.metric("Hot Prospects", f"{metrics.get('hot_prospects_count', 0):,}")

    st.markdown("---")

    # Data freshness warning
    snapshot = get_data_snapshot_info()
    st.warning(f"📅 **Data: {snapshot['date_str']}**")
    st.caption("Recency metrics are relative to this snapshot date, not today.")

    st.markdown("---")
    st.markdown("### 🔬 Analysis Tools")
    st.caption("Use the page selector above for detailed analysis:")
    st.markdown("""
    - **Segment Overview** - Charts & visualizations
    - **Company Explorer** - Deep company profiles
    - **Segment Predictor** - Predict new customer segments
    - **Marketing Playbook** - Original strategies
    """)


# =============================================================================
# ACTION CENTER PAGE
# =============================================================================

def render_action_center():
    """Render the Action-First Sales Command Center"""
    st.markdown('<p class="main-header">🎯 Action Center</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your daily priority queue - what needs attention today</p>', unsafe_allow_html=True)

    # Data freshness notice
    snapshot = get_data_snapshot_info()
    st.info(f"📅 **Data Snapshot: {snapshot['date_str']}** — 'Days since last order' and activity metrics are relative to this date.")

    priorities = get_daily_priorities()
    metrics = priorities.get('metrics', {})

    # Priority metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="priority-card" style="background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);">
            <h3>{metrics.get('high_value_count', 0)}</h3>
            <p>⭐ High-Value Regulars</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="priority-card" style="background: linear-gradient(135deg, #1976D2 0%, #0D47A1 100%);">
            <h3>{metrics.get('growth_potential_count', 0)}</h3>
            <p>📈 Growth Potential</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="priority-card" style="background: linear-gradient(135deg, #C62828 0%, #B71C1C 100%);">
            <h3>{metrics.get('winback_candidates', 0)}</h3>
            <p>🔴 Win-Back Priority</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="priority-card" style="background: linear-gradient(135deg, #7B1FA2 0%, #6A1B9A 100%);">
            <h3>{metrics.get('hot_prospects_count', 0)}</h3>
            <p>🔥 Hot Prospects</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Three columns for priority lists
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔴 Win-Back Priority")
        st.caption("Lapsed Regulars & High-Value Dormant - best recovery ROI")

        at_risk = priorities.get('at_risk', [])
        profiles = load_segment_profiles()
        if at_risk:
            for customer in at_risk[:5]:
                days_ago = customer.get('recency_days', 0)
                years_ago = days_ago / 365
                seg_id = customer.get('ads_cluster', 0)
                seg_name = profiles.get(int(seg_id), {}).get('name', 'Unknown')
                with st.container():
                    st.markdown(f"""
                    <div class="alert-card warning">
                        <strong>{customer['company']}</strong><br/>
                        <small>
                            {seg_name}<br/>
                            Lifetime: £{customer['monetary_total']:,.0f} | {customer['frequency']:.0f} orders<br/>
                            Last order: {years_ago:.1f} years ago
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No win-back candidates identified")

    with col2:
        st.markdown("### 🔥 Hot Prospects")
        st.caption("Ready for outreach")

        hot_prospects = priorities.get('hot_prospects', [])
        if hot_prospects:
            for prospect in hot_prospects[:5]:
                with st.container():
                    st.markdown(f"""
                    <div class="alert-card success">
                        <strong>{prospect['company_name']}</strong><br/>
                        <small>
                            Score: {prospect['prospect_score']:.0f} |
                            {prospect['industry_sector']}<br/>
                            {prospect['region']} | Packaging: {prospect['packaging_need']}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No hot prospects available")

    with col3:
        st.markdown("### 📈 Expansion Opportunities")
        st.caption("Customers with growth potential")

        expansion = priorities.get('expansion', [])
        if expansion:
            for customer in expansion[:5]:
                profiles = load_segment_profiles()
                seg_name = profiles.get(customer['ads_cluster'], {}).get('name', 'Unknown')
                st.markdown(f"""
                <div class="alert-card warning">
                    <strong>{customer['company']}</strong><br/>
                    <small>
                        {seg_name}<br/>
                        Current: £{customer['monetary_total']:,.0f} |
                        Potential: +£{customer['expansion_potential']:,.0f}
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No expansion opportunities identified")


# =============================================================================
# REVENUE OPPORTUNITIES PAGE
# =============================================================================

def render_revenue_opportunities():
    """Render the Revenue Opportunities view"""
    from services.unified_data_service import (
        get_revenue_leakage, get_expansion_opportunities, get_market_gaps
    )

    st.markdown('<p class="main-header">💰 Revenue Opportunities</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Identify and capture revenue - prevent leakage, expand accounts, enter new markets</p>', unsafe_allow_html=True)

    # Summary metrics
    leakage_df = get_revenue_leakage()
    expansion_df = get_expansion_opportunities()

    total_at_risk = leakage_df['revenue_at_stake'].sum() if not leakage_df.empty else 0
    total_expansion = expansion_df['potential_uplift'].sum() if not expansion_df.empty else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Revenue at Risk", f"£{total_at_risk:,.0f}", delta="-requires action", delta_color="inverse")
    with col2:
        st.metric("Expansion Potential", f"£{total_expansion:,.0f}", delta="+opportunity")
    with col3:
        st.metric("Total Opportunity", f"£{total_at_risk + total_expansion:,.0f}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["💸 Revenue Leakage", "📈 Expansion Opportunities", "🗺️ Market Gaps"])

    with tab1:
        st.markdown("### Customers at Risk of Churning")
        st.caption("Prioritized by revenue at stake - take action to retain")

        if not leakage_df.empty:
            # Summary chart
            fig = px.bar(
                leakage_df.head(10),
                x='company',
                y='revenue_at_stake',
                color='churn_risk',
                color_continuous_scale='Reds',
                title='Top 10 Accounts by Revenue at Risk'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            st.dataframe(
                leakage_df.head(20).style.format({
                    'monetary_total': '£{:,.0f}',
                    'revenue_at_stake': '£{:,.0f}',
                    'churn_risk': '{:.0f}%',
                    'recency_days': '{:.0f} days'
                }).background_gradient(subset=['churn_risk'], cmap='Reds'),
                use_container_width=True,
                hide_index=True
            )

            # Export button
            csv = leakage_df.to_csv(index=False)
            st.download_button(
                "📥 Export At-Risk List",
                csv,
                "at_risk_customers.csv",
                "text/csv"
            )
        else:
            st.info("No significant revenue leakage identified")

    with tab2:
        st.markdown("### Accounts with Growth Potential")
        st.caption("Customers performing below their segment average - opportunity to expand")

        if not expansion_df.empty:
            # Chart
            fig = px.bar(
                expansion_df.head(10),
                x='company',
                y=['current_revenue', 'potential_uplift'],
                title='Top 10 Expansion Opportunities',
                barmode='stack',
                color_discrete_map={'current_revenue': '#1976D2', 'potential_uplift': '#4CAF50'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Table
            st.dataframe(
                expansion_df.style.format({
                    'current_revenue': '£{:,.0f}',
                    'segment_avg': '£{:,.0f}',
                    'potential_uplift': '£{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )

            csv = expansion_df.to_csv(index=False)
            st.download_button(
                "📥 Export Expansion List",
                csv,
                "expansion_opportunities.csv",
                "text/csv"
            )
        else:
            st.info("No significant expansion opportunities identified")

    with tab3:
        st.markdown("### Underserved Markets")
        st.caption("Industries and regions with high potential where you're underrepresented")

        gaps_df = get_market_gaps()
        if not gaps_df.empty:
            fig = px.scatter(
                gaps_df,
                x='prospect_count',
                y='avg_score',
                size='high_need_count',
                color='opportunity_score',
                hover_name='industry',
                title='Market Opportunity Analysis',
                labels={
                    'prospect_count': 'Number of Prospects',
                    'avg_score': 'Average ICP Score',
                    'opportunity_score': 'Opportunity'
                }
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(gaps_df, use_container_width=True, hide_index=True)
        else:
            st.info("Unable to analyze market gaps - check prospect data")


# =============================================================================
# PROSPECT PIPELINE PAGE
# =============================================================================

def render_prospect_pipeline():
    """Render the Prospect Pipeline view"""
    from services.unified_data_service import get_best_fit_prospects, load_prospect_data

    st.markdown('<p class="main-header">🔍 Prospect Pipeline</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage your prospect funnel - prioritize high-fit opportunities</p>', unsafe_allow_html=True)

    pipeline = get_prospect_pipeline()
    funnel = pipeline.get('funnel', {})
    prospects_df = pipeline.get('prospects', pd.DataFrame())

    # Funnel visualization
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Prospect Funnel")

        tier_colors = {'Hot': '#C62828', 'Warm': '#F57C00', 'Cool': '#1976D2', 'Cold': '#9E9E9E'}

        for tier in ['Hot', 'Warm', 'Cool', 'Cold']:
            data = funnel.get(tier, {'count': 0, 'avg_score': 0})
            color = tier_colors.get(tier, '#666')
            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; text-align: center;">
                <div style="font-size: 1.5rem; font-weight: bold;">{data['count']}</div>
                <div>{tier} Prospects</div>
                <small>Avg Score: {data['avg_score']:.0f}</small>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Industry breakdown
        by_industry = pipeline.get('by_industry', [])
        if by_industry:
            industry_df = pd.DataFrame(by_industry)
            fig = px.bar(
                industry_df.nlargest(10, 'count'),
                x='industry',
                y='count',
                color='avg_score',
                color_continuous_scale='Greens',
                title='Prospects by Industry'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2 = st.tabs(["⭐ Best-Fit Prospects", "📋 Full Pipeline"])

    with tab1:
        st.markdown("### Best-Fit Prospects")
        st.caption("High packaging need + high ICP score = best opportunities")

        best_fit = get_best_fit_prospects(20)
        if not best_fit.empty:
            # Rename columns for clarity
            display_df = best_fit.rename(columns={
                'company_name': 'Company',
                'industry_sector': 'Industry',
                'region': 'Region',
                'prospect_score': 'ICP Score',
                'priority_tier': 'Tier',
                'packaging_need': 'Pkg Need',
                'industry_score': 'Ind.',
                'age_score': 'Age',
                'size_score': 'Size'
            })

            st.dataframe(
                display_df.style.format({
                    'ICP Score': '{:.0f}',
                    'Ind.': '{:.0f}',
                    'Age': '{:.0f}',
                    'Size': '{:.0f}'
                }).background_gradient(subset=['ICP Score'], cmap='Greens'),
                use_container_width=True,
                hide_index=True
            )

            # Score explanation
            with st.expander("Score Breakdown Explained"):
                st.markdown("""
                - **ICP Score**: Overall fit (0-100) combining all factors
                - **Ind.**: Industry match to KSP's ideal sectors (packaging-intensive)
                - **Age**: Company maturity (7-29 years optimal)
                - **Size**: Business size indicators (officers, filings)
                - **Pkg Need**: HIGH = manufacturing/retail, MEDIUM = services, LOW = other
                """)

            csv = best_fit.to_csv(index=False)
            st.download_button(
                "📥 Export Best-Fit List",
                csv,
                "best_fit_prospects.csv",
                "text/csv"
            )
        else:
            st.info("No best-fit prospects identified")

    with tab2:
        st.markdown("### Full Prospect Pipeline")
        st.caption("Filter and search all 454 pre-scored prospects")

        # Filters in 4 columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            tier_filter = st.multiselect("Tier", ['Hot', 'Warm', 'Cool', 'Cold'], default=['Hot', 'Warm'])
        with col2:
            need_filter = st.multiselect("Packaging Need", ['HIGH', 'MEDIUM', 'LOW'], default=['HIGH', 'MEDIUM'])
        with col3:
            # Get unique industries
            if not prospects_df.empty:
                industries = ['All'] + sorted(prospects_df['industry_sector'].dropna().unique().tolist())
                industry_filter = st.selectbox("Industry", industries)
            else:
                industry_filter = 'All'
        with col4:
            min_score = st.slider("Min ICP Score", 0, 100, 50)

        # Search box
        search_term = st.text_input("Search company name", placeholder="Type to search...")

        if not prospects_df.empty:
            filtered = prospects_df.copy()

            if tier_filter:
                filtered = filtered[filtered['priority_tier'].isin(tier_filter)]
            if need_filter:
                filtered = filtered[filtered['packaging_need'].isin(need_filter)]
            if industry_filter != 'All':
                filtered = filtered[filtered['industry_sector'] == industry_filter]
            if search_term:
                filtered = filtered[filtered['company_name'].str.contains(search_term, case=False, na=False)]
            filtered = filtered[filtered['prospect_score'] >= min_score]

            # Display with more score columns
            display_cols = ['company_name', 'industry_sector', 'region', 'prospect_score',
                          'priority_tier', 'packaging_need', 'industry_score', 'geo_score', 'web_score']
            available_cols = [c for c in display_cols if c in filtered.columns]

            st.dataframe(
                filtered[available_cols].sort_values('prospect_score', ascending=False).head(100).style.format({
                    'prospect_score': '{:.0f}',
                    'industry_score': '{:.0f}',
                    'geo_score': '{:.0f}',
                    'web_score': '{:.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )

            st.caption(f"Showing {min(len(filtered), 100)} of {len(filtered)} matches ({len(prospects_df)} total)")

            # Export filtered results
            if len(filtered) > 0:
                csv = filtered.to_csv(index=False)
                st.download_button(
                    "📥 Export Filtered List",
                    csv,
                    "filtered_prospects.csv",
                    "text/csv"
                )


# =============================================================================
# CUSTOMER EXPLORER PAGE
# =============================================================================

def render_customer_explorer():
    """Render the Customer Explorer view"""
    from services.unified_data_service import (
        search_customers, get_customer_360, get_segment_summary, load_segment_profiles
    )

    st.markdown('<p class="main-header">📊 Customer Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Deep dive into customer segments and individual profiles</p>', unsafe_allow_html=True)

    # Data freshness notice
    snapshot = get_data_snapshot_info()
    st.info(f"📅 **Data Snapshot: {snapshot['date_str']}** — All recency and activity metrics are relative to this date, not today.")

    # Segment summary
    summary_df = get_segment_summary()
    profiles = load_segment_profiles()

    if not summary_df.empty:
        st.markdown("### All 8 Segments Overview")

        # Show segments in 2 rows of 4
        # Row 1: Dormant segments (0-3)
        st.markdown("**Dormant Segments** (Win-back & Re-engagement)")
        cols1 = st.columns(4)
        dormant_segments = summary_df[summary_df['segment_id'].isin([0, 1, 2, 3, 4])].head(4)
        for col, (_, row) in zip(cols1, dormant_segments.iterrows()):
            with col:
                color = row['color']
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 0.75rem; background: white; border-radius: 4px; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.85rem; color: {color}; font-weight: bold;">{row['icon']} {row['name']}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1a1a1a;">{row['count']}</div>
                    <div style="font-size: 0.7rem; color: #555;">{row['pct']:.1f}% | £{row['total_revenue']:,.0f}</div>
                    <div style="font-size: 0.65rem; color: #888; margin-top: 0.25rem;">{row['risk_level']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Row 2: Active segments (4-7)
        st.markdown("**Active Segments** (Protect & Grow)")
        cols2 = st.columns(4)
        active_segments = summary_df[summary_df['segment_id'].isin([4, 5, 6, 7])].tail(4)
        for col, (_, row) in zip(cols2, active_segments.iterrows()):
            with col:
                color = row['color']
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 0.75rem; background: white; border-radius: 4px; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.85rem; color: {color}; font-weight: bold;">{row['icon']} {row['name']}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1a1a1a;">{row['count']}</div>
                    <div style="font-size: 0.7rem; color: #555;">{row['pct']:.1f}% | £{row['total_revenue']:,.0f}</div>
                    <div style="font-size: 0.65rem; color: #888; margin-top: 0.25rem;">{row['risk_level']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Segment comparison chart
        fig = px.bar(
            summary_df,
            x='name',
            y='total_revenue',
            color='name',
            color_discrete_map={row['name']: row['color'] for _, row in summary_df.iterrows()},
            title='Revenue by Segment'
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Search and filter
    st.markdown("### Find Customers")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("Search by company name", placeholder="Enter company name...")
    with col2:
        segment_options = {f"{row['icon']} {row['name']}": row['segment_id'] for _, row in summary_df.iterrows()}
        segment_options = {"All Segments": None} | segment_options
        selected_segment = st.selectbox("Filter by Segment", list(segment_options.keys()))
        segment_filter = segment_options[selected_segment]
    with col3:
        sort_options = {'Revenue (High)': 'monetary_total', 'Frequency': 'frequency', 'Recency': 'recency_days', 'Risk': 'churn_risk'}
        sort_by = st.selectbox("Sort by", list(sort_options.keys()))

    # Search results
    results = search_customers(search_query, segment_filter, sort_options[sort_by])

    if not results.empty:
        st.dataframe(
            results.style.format({
                'monetary_total': '£{:,.0f}',
                'churn_risk': '{:.0f}%'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Customer detail view
        st.markdown("---")
        st.markdown("### Customer 360 View")

        company_list = results['company'].tolist()
        selected_company = st.selectbox("Select customer for details", company_list)

        if selected_company:
            profile = get_customer_360(selected_company)

            if profile:
                col1, col2 = st.columns([1, 2])

                with col1:
                    color = profile['segment_color']
                    st.markdown(f"""
                    <div style="border: 2px solid {color}; border-radius: 12px; padding: 1.5rem; background: white;">
                        <h3 style="color: {color}; margin-top: 0;">{profile['company']}</h3>
                        <span class="segment-pill" style="background: {color};">{profile['segment_name']}</span>
                        <p style="margin-top: 1rem; color: #1a1a1a;"><strong>Risk Level:</strong> {profile['risk_level']}</p>
                        <hr style="border-color: #ddd;"/>
                        <p style="color: #1a1a1a;"><strong>Lifetime Value:</strong> £{profile['lifetime_value']:,.0f}</p>
                        <p style="color: #1a1a1a;"><strong>Churn Risk:</strong> {profile['churn_risk']:.0f}%</p>
                        <p style="color: #1a1a1a;"><strong>Revenue at Stake:</strong> £{profile['revenue_at_stake']:,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("**Recommended Actions:**")
                    for action in profile['recommended_actions']:
                        st.markdown(f"- {action}")

                with col2:
                    # Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Revenue", f"£{profile['total_revenue']:,.0f}")
                    m2.metric("Orders", f"{profile['order_count']:.0f}")
                    m3.metric("Avg Order", f"£{profile['avg_order_value']:,.0f}")
                    m4.metric("Last Order", f"{profile['recency_days']:.0f} days ago")

                    # Engagement chart
                    engagement_data = {
                        'Metric': ['Recency', 'Frequency', 'Monetary', 'Tenure'],
                        'Value': [
                            max(0, 100 - profile['recency_days'] / 3.65),  # Scale to 0-100
                            min(100, profile['order_count'] * 5),
                            min(100, profile['total_revenue'] / 500),
                            min(100, profile['tenure_days'] / 10)
                        ]
                    }
                    fig = px.bar(
                        engagement_data,
                        x='Metric',
                        y='Value',
                        title='Engagement Scores',
                        color='Value',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No customers found. Try adjusting your search criteria.")


# =============================================================================
# COMPANY SEARCH PAGE (Companies House)
# =============================================================================

def render_company_search():
    """Render the Companies House search page"""
    import requests
    import os

    st.markdown('<p class="main-header">🔎 Company Search</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search Companies House to find and score new prospects</p>', unsafe_allow_html=True)

    # Check for API key - try Streamlit secrets first, then environment variable
    api_key = ''
    try:
        api_key = st.secrets.get('COMPANIES_HOUSE_API_KEY', '')
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get('COMPANIES_HOUSE_API_KEY', '')

    if not api_key:
        st.warning("""
        **Companies House API Key Required**

        To search Companies House, you need an API key:
        1. Register at [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
        2. Create an application and get your API key
        3. Add to Streamlit secrets or set environment variable

        For now, you can search the existing prospect database below.
        """)

    st.markdown("---")

    # Search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search company name", placeholder="e.g., Acme Packaging Ltd")
    with col2:
        search_type = st.selectbox("Search in", ["Existing Prospects", "Companies House (API)"])

    if search_term:
        if search_type == "Existing Prospects":
            # Search in existing prospect data
            from services.unified_data_service import load_prospect_data
            prospects = load_prospect_data()

            if not prospects.empty:
                matches = prospects[
                    prospects['company_name'].str.contains(search_term, case=False, na=False)
                ].head(20)

                if not matches.empty:
                    st.success(f"Found {len(matches)} matches in existing prospects")

                    st.dataframe(
                        matches[['company_name', 'industry_sector', 'region', 'prospect_score',
                                'priority_tier', 'packaging_need']].style.format({
                            'prospect_score': '{:.0f}'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No matches in existing prospect database. Try Companies House search.")
            else:
                st.error("Could not load prospect data")

        elif search_type == "Companies House (API)" and api_key:
            # Live Companies House search
            with st.spinner("Searching Companies House..."):
                try:
                    response = requests.get(
                        f"https://api.company-information.service.gov.uk/search/companies",
                        params={"q": search_term, "items_per_page": 20},
                        auth=(api_key, ''),
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])

                        if items:
                            st.success(f"Found {data.get('total_results', len(items))} companies")

                            # Display results
                            for item in items:
                                with st.expander(f"**{item.get('title', 'Unknown')}** - {item.get('company_number', '')}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Status:** {item.get('company_status', 'Unknown')}")
                                        st.write(f"**Type:** {item.get('company_type', 'Unknown')}")
                                        st.write(f"**Created:** {item.get('date_of_creation', 'Unknown')}")

                                    with col2:
                                        address = item.get('address', {})
                                        addr_parts = [
                                            address.get('address_line_1', ''),
                                            address.get('locality', ''),
                                            address.get('region', ''),
                                            address.get('postal_code', '')
                                        ]
                                        st.write(f"**Address:** {', '.join(p for p in addr_parts if p)}")

                                        sic_codes = item.get('sic_codes', [])
                                        if sic_codes:
                                            st.write(f"**SIC Codes:** {', '.join(sic_codes)}")

                                    # Score button (placeholder)
                                    if st.button(f"Add to Prospects", key=f"add_{item.get('company_number')}"):
                                        st.info("To add and score prospects, run the backend API service.")
                        else:
                            st.warning("No companies found matching your search")
                    elif response.status_code == 401:
                        st.error("Invalid API key. Please check your COMPANIES_HOUSE_API_KEY.")
                    else:
                        st.error(f"API error: {response.status_code}")

                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please try again.")
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")

        elif search_type == "Companies House (API)" and not api_key:
            st.error("Please set COMPANIES_HOUSE_API_KEY environment variable to use Companies House search.")

    # Industry filter for existing prospects
    st.markdown("---")
    st.markdown("### Browse by Industry")

    from services.unified_data_service import load_prospect_data
    prospects = load_prospect_data()

    if not prospects.empty:
        industries = sorted(prospects['industry_sector'].dropna().unique().tolist())
        selected_industry = st.selectbox("Select industry to browse", ["Select..."] + industries)

        if selected_industry != "Select...":
            industry_prospects = prospects[prospects['industry_sector'] == selected_industry]
            industry_prospects = industry_prospects.sort_values('prospect_score', ascending=False)

            st.write(f"**{len(industry_prospects)} prospects** in {selected_industry}")

            st.dataframe(
                industry_prospects[['company_name', 'region', 'prospect_score', 'priority_tier',
                                   'packaging_need', 'company_age_years']].head(50).style.format({
                    'prospect_score': '{:.0f}',
                    'company_age_years': '{:.1f} yrs'
                }),
                use_container_width=True,
                hide_index=True
            )


# =============================================================================
# MARKETING PLAYBOOK PAGE
# =============================================================================

def render_marketing_playbook():
    """Render the Marketing Playbook with segment-specific strategies and email templates"""

    st.markdown('<p class="main-header">📧 Marketing Playbook</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Segment-specific marketing strategies and ready-to-use email templates</p>', unsafe_allow_html=True)

    # Marketing Agent Definitions for each segment
    MARKETING_AGENTS = {
        0: {
            "name": "Dormant One-Timer Specialist",
            "persona": "Cost-efficient batch marketer focused on minimal investment re-engagement",
            "strategy": "Low-touch, automated campaigns only. These customers showed minimal commitment - batch emails during seasonal promotions only. Don't invest significant resources.",
            "timing": "Seasonal only (Q4 holidays, spring refresh)",
            "channel": "Email only (batch)",
            "tone": "Friendly reminder, no pressure",
            "kpi": "Cost per re-activation < £5"
        },
        1: {
            "name": "Win-Back Champion",
            "persona": "Relationship rebuilder specializing in lapsed regular customer recovery",
            "strategy": "HIGH PRIORITY. These were loyal customers who stopped. Personal outreach to understand why they left. Offer incentives to return. Survey for feedback.",
            "timing": "Immediate - within 1 week of identification",
            "channel": "Phone call first, then personalized email",
            "tone": "Personal, curious, valued customer",
            "kpi": "Win-back rate > 15%"
        },
        2: {
            "name": "Project Opportunity Hunter",
            "persona": "Project-based sales specialist for occasional buyers",
            "strategy": "These customers buy for specific projects. Stay top-of-mind with capability updates. Check in quarterly about upcoming projects.",
            "timing": "Quarterly check-ins",
            "channel": "Email with phone follow-up",
            "tone": "Helpful, informative, project-focused",
            "kpi": "Project inquiry rate > 10%"
        },
        3: {
            "name": "Re-Engagement Nurture Specialist",
            "persona": "Long-term nurture marketer for moderate history customers",
            "strategy": "Consistent, valuable content to stay relevant. Industry news, product updates, case studies. Build relationship for when need arises.",
            "timing": "Monthly newsletter + quarterly personal touch",
            "channel": "Email nurture sequence",
            "tone": "Professional, informative, patient",
            "kpi": "Engagement rate > 20%"
        },
        4: {
            "name": "VIP Recovery Director",
            "persona": "Executive-level relationship manager for high-value dormant accounts",
            "strategy": "TOP PRIORITY. These were your best customers. Executive outreach, premium return offers, account review meetings. Understand what went wrong.",
            "timing": "URGENT - within 48 hours",
            "channel": "Senior person phone call, then meeting",
            "tone": "Executive, valued partner, concerned",
            "kpi": "Recovery rate > 25%, revenue recovered"
        },
        5: {
            "name": "New Customer Success Manager",
            "persona": "Onboarding specialist focused on new customer development",
            "strategy": "Critical first 90 days. Welcome sequence, product education, first reorder prompt. Build habit and relationship early.",
            "timing": "Immediate welcome, then 30/60/90 day touches",
            "channel": "Email sequence + personal call at day 14",
            "tone": "Welcoming, helpful, educational",
            "kpi": "Second order rate > 40%"
        },
        6: {
            "name": "Growth Acceleration Manager",
            "persona": "Business development specialist for expanding accounts",
            "strategy": "These customers are growing - help them grow faster with you. Cross-sell, upsell, range expansion. Business development calls.",
            "timing": "Monthly touchpoints",
            "channel": "Phone + email + in-person where possible",
            "tone": "Partnership, growth-focused, consultative",
            "kpi": "Account growth > 20% YoY"
        },
        7: {
            "name": "VIP Account Director",
            "persona": "Premium account manager for top-tier customers",
            "strategy": "PROTECT. Dedicated attention, loyalty rewards, priority service, early access to new products. Never let them feel neglected.",
            "timing": "Weekly check-ins, immediate response always",
            "channel": "Dedicated contact, any channel they prefer",
            "tone": "Premium, exclusive, partnership",
            "kpi": "Retention rate > 95%"
        }
    }

    # Email Templates
    EMAIL_TEMPLATES = {
        0: {
            "subject": "Still thinking of you at KSP Packaging",
            "body": """Hi {company_name},

It's been a while since we last worked together, and we wanted to reach out.

At KSP, we've been busy developing new packaging solutions that might be perfect for your next project:
• New sustainable packaging options
• Faster turnaround times
• Competitive pricing for returning customers

If you have any upcoming packaging needs, we'd love to hear from you.

Best regards,
The KSP Team

P.S. As a previous customer, you'll receive 10% off your next order. Just mention this email."""
        },
        1: {
            "subject": "We miss you, {company_name} - let's reconnect",
            "body": """Dear {contact_name},

I noticed it's been over a year since your last order with KSP, and I wanted to personally reach out.

You were one of our valued regular customers, and I'd love to understand what changed. Did we miss something? Has your packaging needs shifted?

I'd genuinely appreciate 5 minutes of your time to:
• Understand if there's anything we could have done better
• Update you on improvements we've made
• Discuss how we might work together again

As a thank you for your time, I'd like to offer you a 15% returning customer discount on your next order.

Could we schedule a quick call this week?

Warm regards,
{sales_rep_name}
Account Manager, KSP Packaging
{phone_number}"""
        },
        2: {
            "subject": "Planning any projects? KSP capabilities update",
            "body": """Hi {company_name},

Hope this finds you well. As we enter a new quarter, I wanted to check in and share some updates from KSP that might be relevant for your upcoming projects.

**New Capabilities:**
• Extended range of sustainable materials
• Enhanced finishing options (foiling, embossing)
• Improved lead times - now as fast as 5 working days

**Recent Project Showcase:**
We recently completed [relevant industry] packaging for [similar company] - happy to share details if interesting.

Do you have any projects on the horizon where we could help? Even if it's early stages, I'd be happy to provide budgetary quotes.

Best regards,
{sales_rep_name}
KSP Packaging"""
        },
        3: {
            "subject": "KSP Packaging Update: Industry trends & new solutions",
            "body": """Hi {company_name},

I hope this message finds you well. I wanted to share some industry insights and updates from KSP that might be valuable for your business.

**Industry Trends:**
• Sustainable packaging demand up 40% - we've expanded our eco-friendly range
• Premium unboxing experiences driving brand loyalty
• Supply chain improvements reducing lead times

**What's New at KSP:**
• New bespoke presentation boxes range
• Enhanced online proofing system
• Extended payment terms available

We'd love to be considered when your next packaging need arises. Feel free to reach out anytime for a no-obligation quote.

Best regards,
The KSP Team"""
        },
        4: {
            "subject": "Personal message from KSP Leadership - {company_name}",
            "body": """Dear {contact_name},

I'm reaching out personally because {company_name} has been one of KSP's most valued customers, and I noticed we haven't had the pleasure of working together recently.

Your business meant a great deal to us - not just commercially, but as a partnership we genuinely valued. I wanted to understand directly: is there anything we could have done better?

I'd like to offer:
• A personal account review meeting at your convenience
• A dedicated account manager going forward
• Preferred pricing reflecting your history with us
• Priority production slots for your orders

Your feedback would be invaluable to me, whether or not you choose to work with us again.

Could I arrange a call or meeting this week?

With sincere regards,
{senior_name}
{senior_title}, KSP Packaging
{direct_line}"""
        },
        5: {
            "subject": "Welcome to KSP! Here's what happens next...",
            "body": """Hi {company_name},

Welcome to KSP Packaging! We're thrilled to have you as a customer.

**Your Recent Order:**
Thank you for order #{order_number}. Here's what to expect:
• Production timeline: {timeline}
• Delivery date: {delivery_date}
• Your dedicated contact: {rep_name} ({rep_email})

**Getting the Most from KSP:**
• View our full product range: [link]
• Request samples: [link]
• Need help? Call us: {phone}

**New Customer Offer:**
Order again within 30 days and receive 10% off your second order - our way of saying thank you for choosing KSP.

Any questions at all, please don't hesitate to reach out.

Welcome aboard!
{rep_name}
KSP Packaging"""
        },
        6: {
            "subject": "Ideas for {company_name} - let's explore growth together",
            "body": """Hi {contact_name},

I've been reviewing your account and I'm excited about the growth we've seen together. I wanted to share some ideas that might help accelerate your packaging strategy.

**Opportunities I've Identified:**
• Based on your current orders, you might benefit from our {product_suggestion}
• Customers similar to you have seen success with {cross_sell_item}
• Volume pricing could reduce your costs by approximately {savings_estimate}

**Business Development Meeting:**
I'd love to schedule a 30-minute call to:
• Review your upcoming needs and plans
• Explore product range expansion opportunities
• Discuss volume arrangements that could benefit both of us

Would next week work for a call?

Looking forward to continuing our partnership,
{rep_name}
Business Development, KSP Packaging"""
        },
        7: {
            "subject": "Your VIP status at KSP - {company_name}",
            "body": """Dear {contact_name},

As one of KSP's most valued partners, I wanted to personally ensure you're receiving the premium service you deserve.

**Your VIP Benefits:**
• Dedicated account manager: {rep_name} (direct: {direct_line})
• Priority production scheduling
• Extended payment terms
• Early access to new products and materials
• Complimentary samples and prototyping

**Exclusive Offer:**
We're launching a new premium range next month. As a VIP customer, you're invited to an exclusive preview and first access to orders.

**Standing Invitation:**
Please remember - for anything urgent, my direct line is always available to you: {direct_line}

Is there anything we could be doing better for you? Your feedback shapes how we serve our best customers.

With appreciation,
{senior_rep_name}
VIP Accounts Director, KSP Packaging"""
        }
    }

    # Segment names for display
    SEGMENT_NAMES = {
        0: "Dormant One-Timers",
        1: "Lapsed Regulars",
        2: "Occasional Past",
        3: "Moderate History",
        4: "High-Value Dormant",
        5: "New Prospects",
        6: "Growth Potential",
        7: "High-Value Regulars"
    }

    SEGMENT_COLORS = {
        0: "#9E9E9E", 1: "#E91E63", 2: "#9C27B0", 3: "#673AB7",
        4: "#C62828", 5: "#00BCD4", 6: "#1976D2", 7: "#2E7D32"
    }

    # Tab selection
    tab1, tab2, tab3 = st.tabs(["📋 Strategy Overview", "📧 Email Templates", "🎯 Segment Deep Dive"])

    with tab1:
        st.markdown("### Marketing Strategy by Segment")
        st.markdown("Each segment requires a different approach. Here's the expert strategy for each:")

        # Priority order for display
        priority_order = [4, 1, 7, 6, 5, 2, 3, 0]  # Highest priority first

        for seg_id in priority_order:
            agent = MARKETING_AGENTS[seg_id]
            color = SEGMENT_COLORS[seg_id]

            with st.expander(f"**{SEGMENT_NAMES[seg_id]}** - {agent['name']}", expanded=(seg_id in [4, 1, 7])):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Strategy:** {agent['strategy']}")
                    st.markdown(f"**Tone:** {agent['tone']}")

                with col2:
                    st.markdown(f"**Timing:** {agent['timing']}")
                    st.markdown(f"**Channel:** {agent['channel']}")
                    st.markdown(f"**Target KPI:** {agent['kpi']}")

    with tab2:
        st.markdown("### Ready-to-Use Email Templates")
        st.markdown("Select a segment to view and copy the email template:")

        selected_segment = st.selectbox(
            "Select Segment",
            options=list(SEGMENT_NAMES.keys()),
            format_func=lambda x: f"{SEGMENT_NAMES[x]}"
        )

        if selected_segment is not None:
            template = EMAIL_TEMPLATES[selected_segment]
            agent = MARKETING_AGENTS[selected_segment]

            st.markdown(f"#### {SEGMENT_NAMES[selected_segment]}")
            st.markdown(f"*{agent['persona']}*")

            st.markdown("---")

            st.markdown(f"**Subject Line:**")
            st.code(template['subject'], language=None)

            st.markdown(f"**Email Body:**")
            st.code(template['body'], language=None)

            # Copy buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download Template",
                    f"Subject: {template['subject']}\n\n{template['body']}",
                    f"email_template_{SEGMENT_NAMES[selected_segment].lower().replace(' ', '_')}.txt",
                    "text/plain"
                )

            st.markdown("---")
            st.markdown("**Personalization Variables:**")
            st.markdown("""
            Replace these placeholders before sending:
            - `{company_name}` - Customer company name
            - `{contact_name}` - Contact person's name
            - `{sales_rep_name}` - Your name
            - `{phone_number}` - Your contact number
            - `{order_number}` - Relevant order number
            """)

    with tab3:
        st.markdown("### Segment Deep Dive")

        from services.unified_data_service import get_segment_summary, load_customer_data

        summary_df = get_segment_summary()
        customers = load_customer_data()

        if not summary_df.empty:
            selected_deep_dive = st.selectbox(
                "Select segment for detailed view",
                options=list(SEGMENT_NAMES.keys()),
                format_func=lambda x: f"{SEGMENT_NAMES[x]}",
                key="deep_dive_select"
            )

            if selected_deep_dive is not None:
                seg_data = summary_df[summary_df['segment_id'] == selected_deep_dive]
                agent = MARKETING_AGENTS[selected_deep_dive]

                if not seg_data.empty:
                    row = seg_data.iloc[0]

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Customers", f"{row['count']:,}")
                    col2.metric("Total Revenue", f"£{row['total_revenue']:,.0f}")
                    col3.metric("Avg Recency", f"{row['avg_recency']:.0f} days")

                st.markdown("---")
                st.markdown(f"### Marketing Agent: {agent['name']}")
                st.markdown(f"*{agent['persona']}*")

                st.markdown(f"""
                **Full Strategy Brief:**

                {agent['strategy']}

                **Execution Details:**
                - **Timing:** {agent['timing']}
                - **Primary Channel:** {agent['channel']}
                - **Communication Tone:** {agent['tone']}
                - **Success Metric:** {agent['kpi']}
                """)

                # Show sample customers from this segment
                if not customers.empty and 'ads_cluster' in customers.columns:
                    seg_customers = customers[customers['ads_cluster'] == selected_deep_dive].head(10)
                    if not seg_customers.empty:
                        st.markdown("---")
                        st.markdown("**Sample Customers in This Segment:**")
                        display_cols = ['company', 'monetary_total', 'frequency', 'recency_days']
                        available = [c for c in display_cols if c in seg_customers.columns]
                        st.dataframe(
                            seg_customers[available].style.format({
                                'monetary_total': '£{:,.0f}',
                                'recency_days': '{:.0f} days'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )


# =============================================================================
# MAIN ROUTING
# =============================================================================

def main():
    if page == "🎯 Action Center":
        render_action_center()
    elif page == "💰 Revenue Opportunities":
        render_revenue_opportunities()
    elif page == "🔍 Prospect Pipeline":
        render_prospect_pipeline()
    elif page == "📊 Customer Explorer":
        render_customer_explorer()
    elif page == "🔎 Company Search":
        render_company_search()
    elif page == "📧 Marketing Playbook":
        render_marketing_playbook()


if __name__ == "__main__":
    main()
