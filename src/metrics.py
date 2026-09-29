"""
Metrics calculation engine for the CDC Natality Dashboard.

Computes descriptive aggregates strictly from observed birth counts.
No demographic rates or ungrounded statistics are derived.
"""

from typing import Dict, Any, Tuple
import pandas as pd


def compute_kpis(filtered_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes summary KPIs for the filtered dataset slice.
    Handles empty slices gracefully.
    """
    if filtered_df.empty:
        return {
            "total_births": 0,
            "geography_count": 0,
            "selected_months_count": 0,
            "avg_births_per_month": 0.0,
            "top_geography": "None",
            "top_geography_births": 0,
            "top_month": "None",
            "top_month_births": 0,
            "female_births": 0,
            "male_births": 0,
            "pct_female": 0.0,
            "pct_male": 0.0,
        }

    total_births = int(filtered_df["Births"].sum())
    geo_count = filtered_df["State of Residence"].nunique()
    months_count = filtered_df["Month"].nunique()

    # Average births per selected month (sum of births / count of selected months)
    avg_per_month = total_births / months_count if months_count > 0 else 0.0

    # Geography with highest selected birth count
    geo_totals = filtered_df.groupby("State of Residence")["Births"].sum()
    top_geo = geo_totals.idxmax() if not geo_totals.empty else "N/A"
    top_geo_births = int(geo_totals.max()) if not geo_totals.empty else 0

    # Month with highest selected birth count
    month_totals = filtered_df.groupby("Month", observed=True)["Births"].sum()
    top_month = str(month_totals.idxmax()) if not month_totals.empty else "N/A"
    top_month_births = int(month_totals.max()) if not month_totals.empty else 0

    # Sex breakdown
    sex_totals = filtered_df.groupby("Sex of Infant")["Births"].sum().to_dict()
    female_births = int(sex_totals.get("Female", 0))
    male_births = int(sex_totals.get("Male", 0))
    pct_female = (female_births / total_births * 100) if total_births > 0 else 0.0
    pct_male = (male_births / total_births * 100) if total_births > 0 else 0.0

    return {
        "total_births": total_births,
        "geography_count": geo_count,
        "selected_months_count": months_count,
        "avg_births_per_month": avg_per_month,
        "top_geography": top_geo,
        "top_geography_births": top_geo_births,
        "top_month": top_month,
        "top_month_births": top_month_births,
        "female_births": female_births,
        "male_births": male_births,
        "pct_female": pct_female,
        "pct_male": pct_male,
    }


def get_top_and_bottom_geographies(
    filtered_df: pd.DataFrame, n: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns the top N and bottom N states by aggregate birth counts.
    """
    if filtered_df.empty:
        empty_df = pd.DataFrame(columns=["State of Residence", "Births"])
        return empty_df, empty_df

    state_totals = (
        filtered_df.groupby("State of Residence", as_index=False)["Births"]
        .sum()
        .sort_values(by="Births", ascending=False)
    )

    top_n = state_totals.head(n).copy()
    bottom_n = state_totals.tail(n).iloc[::-1].copy()  # Lowest first

    return top_n, bottom_n
