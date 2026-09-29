"""
CDC 2025 Provisional Natality Dashboard
=======================================
An interactive exploratory dashboard for undergraduate business analytics students.
Provides exploratory analysis across geographic, monthly, and sex-based birth counts.

Designed to illustrate:
1. Exploratory data analysis (EDA) workflows.
2. Data quality auditing and verification.
3. Separation of counts vs. population rates.
4. Clean software architecture with modular Python components.
"""

from typing import List, Tuple
import pandas as pd
import streamlit as st

from src.config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    SOURCE_ATTRIBUTION,
    PROVISIONAL_NOTICE,
    COUNT_VS_RATE_NOTICE,
    CALENDAR_MONTHS,
    EXPECTED_AUDIT,
)
from src.data_loader import load_and_preprocess_data, DataValidationError
from src.metrics import compute_kpis, get_top_and_bottom_geographies
from src.charts import (
    create_monthly_trend_chart,
    create_sex_comparison_chart,
    create_state_ranking_chart,
    create_choropleth_map,
    create_top_bottom_chart,
    create_state_month_heatmap,
)


def init_page_config() -> None:
    """Configures Streamlit page metadata and responsive layout."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    """Injects accessible custom CSS for polished styling and clean KPI cards."""
    st.markdown(
        """
        <style>
        /* Modern font & container spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        /* KPI Metric Card Styling */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 1rem 1.25rem;
            border-radius: 0.6rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stMetric"]:hover {
            border-color: #CBD5E1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease-in-out;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            color: #64748B !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            color: #0F172A !important;
            font-weight: 700 !important;
        }
        /* Callout Banners */
        .notice-badge {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            font-weight: 600;
            border-left: 4px solid #F59E0B;
            margin-bottom: 0.6rem;
        }
        .concept-badge {
            background-color: #EFF6FF;
            color: #1E40AF;
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            font-weight: 500;
            border-left: 4px solid #3B82F6;
            margin-bottom: 1.2rem;
        }
        /* Sidebar active summary */
        .filter-summary-box {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 0.5rem;
            padding: 0.75rem;
            margin-top: 1rem;
            font-size: 0.85rem;
            color: #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Renders the dashboard header, provenance notice, and pedagogical disclaimers."""
    st.title("📊 Provisional 2025 CDC Natality Dashboard")
    st.markdown(
        "An exploratory analytics application designed for studying state-level, monthly, "
        "and sex-based birth counts across the United States."
    )
    # Notice & Concept Badges
    st.markdown(f'<div class="notice-badge">{PROVISIONAL_NOTICE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="concept-badge">{COUNT_VS_RATE_NOTICE}</div>', unsafe_allow_html=True)


def init_filter_session_state(all_states: List[str], all_months: List[str]) -> None:
    """Initializes session state defaults for interactive filters."""
    if "ms_states" not in st.session_state:
        st.session_state["ms_states"] = list(all_states)
    if "ms_months" not in st.session_state:
        st.session_state["ms_months"] = list(all_months)
    if "radio_sex" not in st.session_state:
        st.session_state["radio_sex"] = "All"


def cb_reset_filters(all_states: List[str], all_months: List[str]) -> None:
    """Callback to restore all filter controls to their default state."""
    st.session_state["ms_states"] = list(all_states)
    st.session_state["ms_months"] = list(all_months)
    st.session_state["radio_sex"] = "All"


def cb_select_all_states(all_states: List[str]) -> None:
    """Callback to select all 51 geographies."""
    st.session_state["ms_states"] = list(all_states)


def cb_clear_all_states() -> None:
    """Callback to deselect all geographies."""
    st.session_state["ms_states"] = []


def cb_select_all_months(all_months: List[str]) -> None:
    """Callback to select all 12 calendar months."""
    st.session_state["ms_months"] = list(all_months)


def cb_clear_all_months() -> None:
    """Callback to deselect all months."""
    st.session_state["ms_months"] = []


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renders filter controls with Select All, Reset, and dynamic summary.
    Returns the filtered dataframe slice.
    """
    all_states = sorted(df["State of Residence"].unique().tolist())
    all_months = CALENDAR_MONTHS

    init_filter_session_state(all_states, all_months)

    st.sidebar.header("🔍 Filter Controls")

    # Reset Filters Button with callback
    st.sidebar.button(
        "🔄 Reset All Filters",
        use_container_width=True,
        type="secondary",
        on_click=cb_reset_filters,
        args=(all_states, all_months),
    )

    st.sidebar.markdown("---")

    # 1. State / Geography Selection
    st.sidebar.subheader("1. Geography")
    col_state_all, col_state_clear = st.sidebar.columns(2)
    col_state_all.button(
        "Select All",
        key="btn_all_states",
        use_container_width=True,
        on_click=cb_select_all_states,
        args=(all_states,),
    )
    col_state_clear.button(
        "Clear All",
        key="btn_clear_states",
        use_container_width=True,
        on_click=cb_clear_all_states,
    )

    selected_states = st.sidebar.multiselect(
        "Choose Geographies (50 States + DC):",
        options=all_states,
        key="ms_states",
        help="Filter birth counts by state or federal district of maternal residence."
    )

    st.sidebar.markdown("---")

    # 2. Month Selection (Strict Chronological Order)
    st.sidebar.subheader("2. Calendar Month")
    col_mo_all, col_mo_clear = st.sidebar.columns(2)
    col_mo_all.button(
        "Select All",
        key="btn_all_months",
        use_container_width=True,
        on_click=cb_select_all_months,
        args=(all_months,),
    )
    col_mo_clear.button(
        "Clear All",
        key="btn_clear_months",
        use_container_width=True,
        on_click=cb_clear_all_months,
    )

    selected_months = st.sidebar.multiselect(
        "Choose Months (Chronological):",
        options=all_months,
        key="ms_months",
        help="Filter births by month of occurrence in calendar year 2025."
    )

    st.sidebar.markdown("---")

    # 3. Infant-Sex Selection
    st.sidebar.subheader("3. Infant Sex")
    sex_options = ["All", "Female", "Male"]
    selected_sex = st.sidebar.radio(
        "Filter by Recorded Infant Sex:",
        options=sex_options,
        key="radio_sex",
        horizontal=True,
    )

    # Apply Filtering Logic
    filtered_df = df.copy()
    if selected_states:
        filtered_df = filtered_df[filtered_df["State of Residence"].isin(selected_states)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_months:
        filtered_df = filtered_df[filtered_df["Month"].isin(selected_months)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_sex != "All":
        filtered_df = filtered_df[filtered_df["Sex of Infant"] == selected_sex]


    # Active Filters Summary Box
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Active Filters Summary")
    st.sidebar.markdown(
        f"""
        <div class="filter-summary-box">
            <b>Geographies:</b> {len(selected_states)} of {len(all_states)}<br>
            <b>Months:</b> {len(selected_months)} of {len(all_months)}<br>
            <b>Infant Sex:</b> {selected_sex}<br>
            <b>Matching Rows:</b> {len(filtered_df):,} observations
        </div>
        """,
        unsafe_allow_html=True,
    )

    return filtered_df


def render_kpi_cards(kpis: dict) -> None:
    """Renders 5 top-level KPI cards with thousands formatting."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Births",
            value=f"{kpis['total_births']:,}",
            help="Total live births recorded across the active filter selection."
        )
    with col2:
        st.metric(
            label="Selected Geographies",
            value=f"{kpis['geography_count']} / 51",
            help="Number of US states (plus DC) included in the current selection."
        )
    with col3:
        st.metric(
            label="Avg Births / Month",
            value=f"{round(kpis['avg_births_per_month']):,}",
            help="Mean aggregate births recorded per selected month."
        )
    with col4:
        st.metric(
            label="Peak Geography",
            value=kpis["top_geography"],
            delta=f"{kpis['top_geography_births']:,} births" if kpis["top_geography_births"] > 0 else None,
            delta_color="off",
            help="Geography with the largest total birth volume in the current selection."
        )
    with col5:
        st.metric(
            label="Peak Month",
            value=kpis["top_month"],
            delta=f"{kpis['top_month_births']:,} births" if kpis["top_month_births"] > 0 else None,
            delta_color="off",
            help="Calendar month with the highest aggregate birth count in the current selection."
        )


def render_overview_tab(filtered_df: pd.DataFrame, kpis: dict) -> None:
    """Renders Tab 1: Overview and high-level trends."""
    st.markdown("### 📈 Executive Overview: 2025 Natality Landscape")
    st.markdown(
        "Explore monthly trajectory and geographic distribution across selected criteria. "
        "Notice seasonal peaks and the proportion of male to female births."
    )

    col_trend, col_map = st.columns([1, 1])

    with col_trend:
        fig_trend = create_monthly_trend_chart(filtered_df)
        st.plotly_chart(fig_trend, key="overview_trend_chart")

    with col_map:
        fig_map = create_choropleth_map(filtered_df)
        st.plotly_chart(fig_map, key="overview_map_chart")

    # Sub-row: Sex Breakdown Summary
    st.markdown("#### 👶 Recorded Infant Sex Distribution in Selection")
    col_fem, col_male, col_notes = st.columns([1, 1, 2])
    with col_fem:
        st.metric(
            label="Female Births",
            value=f"{kpis['female_births']:,}",
            delta=f"{kpis['pct_female']:.2f}% of selection",
            delta_color="off"
        )
    with col_male:
        st.metric(
            label="Male Births",
            value=f"{kpis['male_births']:,}",
            delta=f"{kpis['pct_male']:.2f}% of selection",
            delta_color="off"
        )
    with col_notes:
        st.info(
            "💡 **Analytics Takeaway for Students**: Human biological sex ratios at birth "
            "consistently show approximately 104–105 male births per 100 female births (~51.2% male). "
            "Compare this expected biological benchmark with the audited 2025 CDC figures."
        )


def render_geographic_tab(filtered_df: pd.DataFrame) -> None:
    """Renders Tab 2: Geographic Analysis."""
    st.markdown("### 🗺️ Geographic Analysis & Volume Disparities")
    st.markdown(
        "Analyze geographic concentration of births across states and federal districts. "
        "Keep in mind that high counts strongly correlate with total state population."
    )

    # Choropleth Map (Full Width)
    fig_map = create_choropleth_map(filtered_df)
    st.plotly_chart(fig_map, key="geo_full_map_chart")

    col_rank, col_compare = st.columns([1.1, 0.9])

    with col_rank:
        st.markdown("#### 📊 Full Geographic Rankings")
        fig_rank = create_state_ranking_chart(filtered_df)
        st.plotly_chart(fig_rank, key="geo_rankings_chart")

    with col_compare:
        st.markdown("#### ⚖️ High-Volume vs. Low-Volume States")
        fig_top_bottom = create_top_bottom_chart(filtered_df, n=5)
        st.plotly_chart(fig_top_bottom, key="geo_top_bottom_chart")
        st.caption(
            "📌 Note how population giants (e.g., California, Texas, Florida) dominate total counts, "
            "while smaller jurisdictions (e.g., Vermont, Wyoming) record counts below 1,000 per month."
        )


def render_monthly_sex_tab(filtered_df: pd.DataFrame) -> None:
    """Renders Tab 3: Monthly & Sex Analysis."""
    st.markdown("### 📅 Monthly Patterns & Infant-Sex Analysis")
    st.markdown(
        "Examine seasonal birth shifts across 2025 and evaluate consistency between female and male births."
    )

    col_sex_chart, col_heatmap = st.columns([1, 1])

    with col_sex_chart:
        fig_sex = create_sex_comparison_chart(filtered_df)
        st.plotly_chart(fig_sex, key="monthly_sex_comparison_chart")

    with col_heatmap:
        st.markdown("#### 🌡️ State × Month Birth Intensity Matrix")
        fig_heat = create_state_month_heatmap(filtered_df)
        st.plotly_chart(fig_heat, key="monthly_heatmap_chart")



def render_data_table_tab(filtered_df: pd.DataFrame) -> None:
    """Renders Tab 4: Searchable data grid and CSV export utility."""
    st.markdown("### 💾 Filtered Data Access & Export")
    st.markdown(
        "Inspect the underlying records for the active filter selection. "
        "You can search, sort by any column, or download the filtered dataset as a CSV file."
    )

    # Data Summary Bar
    st.write(f"Displaying **{len(filtered_df):,}** observations | Total Births: **{filtered_df['Births'].sum():,}**")

    # Display clean table
    display_df = filtered_df[
        ["State of Residence", "State Code", "Month", "Month Code", "Year Code", "Sex of Infant", "Births"]
    ].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Births": st.column_config.NumberColumn("Births", format="%d"),
            "Month Code": st.column_config.NumberColumn("Month Code", format="%d"),
            "Year Code": st.column_config.NumberColumn("Year Code", format="%d"),
        },
    )

    # CSV Export Button
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="cdc_provisional_natality_2025_filtered.csv",
        mime="text/csv",
        help="Download the currently filtered records as a standard CSV spreadsheet.",
        type="primary",
    )


def render_about_tab(audit_summary: dict) -> None:
    """Renders Tab 5: Data provenance, audit proof, and student educational guide."""
    st.markdown("### 📖 About the Dataset & Business Analytics Guide")

    st.markdown(
        """
        #### 1. What Does "Provisional Data" Mean?
        In public health informatics, **provisional natality data** represent vital records reported by 
        state vital statistics reporting offices to the CDC's **National Center for Health Statistics (NCHS)** 
        prior to final annual reconciliation. 
        - Provisional reports offer timely visibility into emerging demographic patterns.
        - However, figures remain subject to late reporting, retrospective corrections, and administrative updates.
        
        #### 2. Critical Distinction: Birth Counts vs. Birth Rates
        A fundamental pitfall in business analytics is confounding **volume (counts)** with **propensity (rates)**:
        - **Birth Count ($N$)**: The absolute number of live births recorded in a jurisdiction during a timeframe.
        - **Crude Birth Rate**: Live births per $1,000$ total population:
          $$\\text{Crude Birth Rate} = \\frac{\\text{Total Live Births}}{\\text{Total Resident Population}} \\times 1,000$$
        - **General Fertility Rate**: Live births per $1,000$ women of childbearing age ($15-44$ years).
        
        > ⚠️ **Key Takeaway**: Because this dataset provides *only* birth counts without resident population denominators, 
        > you cannot conclude that women in California or Texas are "having more babies per capita" than women in Vermont. 
        > High birth counts primarily reflect large population scale!
        
        #### 3. Data Integrity & Verification Audit
        Before loading, our data pipeline rigorously audits the workbook against expected benchmarks:
        """
    )

    audit_table_data = [
        {"Criterion": "Total Observations (Rows)", "Expected": f"{EXPECTED_AUDIT['observations']:,}", "Audited Result": f"{audit_summary['observations']:,}", "Verification": "✅ Pass"},
        {"Criterion": "Geographies (50 States + DC)", "Expected": f"{EXPECTED_AUDIT['geographies']}", "Audited Result": f"{audit_summary['geographies']}", "Verification": "✅ Pass"},
        {"Criterion": "Calendar Months", "Expected": f"{EXPECTED_AUDIT['months']}", "Audited Result": f"{audit_summary['months']}", "Verification": "✅ Pass"},
        {"Criterion": "Infant-Sex Categories", "Expected": f"{EXPECTED_AUDIT['sexes']}", "Audited Result": f"{audit_summary['sexes']}", "Verification": "✅ Pass"},
        {"Criterion": "Missing Values (Nulls)", "Expected": f"{EXPECTED_AUDIT['missing']}", "Audited Result": f"{audit_summary['missing']}", "Verification": "✅ Pass"},
        {"Criterion": "Duplicate Records", "Expected": f"{EXPECTED_AUDIT['duplicates']}", "Audited Result": f"{audit_summary['duplicates']}", "Verification": "✅ Pass"},
        {"Criterion": "Total National Births", "Expected": f"{EXPECTED_AUDIT['total_births']:,}", "Audited Result": f"{audit_summary['total_births']:,}", "Verification": "✅ Pass"},
    ]
    st.table(pd.DataFrame(audit_table_data))

    st.markdown(
        f"""
        #### 4. Source Citation
        > **CDC WONDER / NCHS**: Centers for Disease Control and Prevention, National Center for Health Statistics.  
        > *Provisional Natality Statistics on CDC WONDER Online Database, 2025*.
        """
    )


def main() -> None:
    """Main application lifecycle."""
    init_page_config()
    inject_custom_css()

    # Load and validate dataset
    try:
        df, audit_summary = load_and_preprocess_data()
    except DataValidationError as e:
        st.error(f"🛑 Critical Data Validation Failure: {e}")
        st.stop()
    except Exception as e:
        st.error(f"🛑 Unable to load dataset: {e}")
        st.stop()

    render_header()

    # Sidebar Filter Controls
    filtered_df = render_sidebar_filters(df)

    # Empty Filter Guardrail
    if filtered_df.empty:
        st.warning(
            "⚠️ **No observations match your current filter selection.**\n\n"
            "Please select at least one geography, one month, and ensure the infant sex filter is active. "
            "Use the **'Reset All Filters'** button in the sidebar to restore defaults."
        )
        st.stop()

    # Compute KPI metrics
    kpis = compute_kpis(filtered_df)

    # Render KPI Cards
    render_kpi_cards(kpis)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation Tabs
    tab_overview, tab_geo, tab_monthly, tab_table, tab_about = st.tabs(
        [
            "📈 Overview",
            "🗺️ Geographic Analysis",
            "📅 Monthly & Sex Analysis",
            "💾 Data Table & Download",
            "📖 About the Data",
        ]
    )

    with tab_overview:
        render_overview_tab(filtered_df, kpis)

    with tab_geo:
        render_geographic_tab(filtered_df)

    with tab_monthly:
        render_monthly_sex_tab(filtered_df)

    with tab_table:
        render_data_table_tab(filtered_df)

    with tab_about:
        render_about_tab(audit_summary)

    # Footer
    st.markdown("---")
    st.caption(f"{SOURCE_ATTRIBUTION} | Prepared for Business Analytics Students.")


if __name__ == "__main__":
    main()
