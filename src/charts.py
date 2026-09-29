"""
Plotly chart generation module for CDC Natality Dashboard.

Best practices for beginning business analytics students:
- Bar charts strictly anchor at zero to prevent visual distortion.
- Calendar months are arranged in strict chronological sequence (January through December).
- Data points and tooltips display commas for readability.
- High-contrast, colorblind-friendly palettes are used throughout.
"""

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import CALENDAR_MONTHS, COLORS


def _apply_standard_layout(
    fig: go.Figure,
    title: str,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    height: int = 420
) -> go.Figure:
    """Helper to enforce clean, consistent design typography and margins."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "y": 0.95,
            "x": 0.02,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 16, "color": COLORS["neutral_dark"]}
        },
        font={"family": "Inter, Segoe UI, Roboto, sans-serif", "size": 12, "color": COLORS["neutral_dark"]},
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin={"l": 50, "r": 30, "t": 60, "b": 50},
        height=height,
        hoverlabel={"bgcolor": "white", "font_size": 13, "font_family": "Inter, sans-serif"},
    )
    if xaxis_title:
        fig.update_xaxes(title_text=xaxis_title, showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    if yaxis_title:
        fig.update_yaxes(title_text=yaxis_title, showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    return fig


def create_monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Renders an interactive monthly line chart with visible data markers.
    Preserves calendar month sequence and sets y-axis baseline to 0.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "Monthly Birth Volume (No Data Available)")

    monthly_data = (
        df.groupby(["Month Code", "Month"], observed=True)["Births"]
        .sum()
        .reset_index()
        .sort_values(by="Month Code")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly_data["Month"],
            y=monthly_data["Births"],
            mode="lines+markers+text",
            name="Total Births",
            line={"color": COLORS["secondary"], "width": 3},
            marker={"size": 8, "color": COLORS["primary"], "symbol": "circle"},
            text=[f"{val:,}" for val in monthly_data["Births"]],
            textposition="top center",
            textfont={"size": 10, "color": COLORS["neutral_dark"]},
            hovertemplate="<b>%{x} 2025</b><br>Total Births: <b>%{y:,}</b><extra></extra>",
        )
    )

    max_val = monthly_data["Births"].max() if not monthly_data.empty else 1000
    _apply_standard_layout(
        fig,
        title="2025 Monthly Birth Count Trend",
        xaxis_title="Month",
        yaxis_title="Total Live Births (Count)",
        height=400
    )
    # Ensure baseline starts at 0 for truthful scaling without visual exaggeration
    fig.update_yaxes(range=[0, max_val * 1.15], tickformat=",")
    return fig


def create_sex_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """
    Renders a grouped bar chart comparing Female and Male births across months.
    Bars strictly start at zero with accessible colors.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "Infant Sex Comparison (No Data Available)")

    grouped = (
        df.groupby(["Month Code", "Month", "Sex of Infant"], observed=True)["Births"]
        .sum()
        .reset_index()
        .sort_values(by=["Month Code", "Sex of Infant"])
    )

    fig = go.Figure()
    color_map = {"Female": COLORS["female"], "Male": COLORS["male"]}

    for sex in ["Female", "Male"]:
        sex_slice = grouped[grouped["Sex of Infant"] == sex]
        fig.add_trace(
            go.Bar(
                x=sex_slice["Month"],
                y=sex_slice["Births"],
                name=f"{sex} Infants",
                marker_color=color_map[sex],
                hovertemplate="<b>%{x}</b><br>Sex: " + sex + "<br>Births: <b>%{y:,}</b><extra></extra>",
            )
        )

    fig.update_layout(barmode="group", legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1})
    _apply_standard_layout(
        fig,
        title="Monthly Birth Counts by Infant Sex",
        xaxis_title="Month",
        yaxis_title="Live Births (Count)",
        height=400
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    return fig


def create_state_ranking_chart(df: pd.DataFrame, max_states: int = 51) -> go.Figure:
    """
    Renders a horizontal bar chart of states ranked by total births.
    Sorted descending, with baseline anchored at 0.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "State Rankings (No Data Available)")

    ranked = (
        df.groupby("State of Residence", as_index=False)["Births"]
        .sum()
        .sort_values(by="Births", ascending=True)  # ascending for horizontal bar (top at top)
    )

    if len(ranked) > max_states:
        ranked = ranked.tail(max_states)

    chart_height = max(400, len(ranked) * 22 + 100)

    fig = go.Figure(
        go.Bar(
            x=ranked["Births"],
            y=ranked["State of Residence"],
            orientation="h",
            marker={
                "color": ranked["Births"],
                "colorscale": "Blues",
                "showscale": False
            },
            hovertemplate="<b>%{y}</b><br>Total Births: <b>%{x:,}</b><extra></extra>",
        )
    )

    _apply_standard_layout(
        fig,
        title=f"Total Birth Counts by Geography (Selected: {len(ranked)})",
        xaxis_title="Total Live Births (Count)",
        yaxis_title="State / Geography",
        height=chart_height
    )
    fig.update_xaxes(rangemode="tozero", tickformat=",")
    return fig


def create_choropleth_map(df: pd.DataFrame) -> go.Figure:
    """
    Generates a US choropleth map displaying aggregate birth counts by state.
    Uses reliable two-letter postal codes for Plotly's USA-states geometry.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "Geographic Distribution (No Data Available)")

    state_totals = (
        df.groupby(["State of Residence", "State Code"], as_index=False)["Births"]
        .sum()
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=state_totals["State Code"],
            z=state_totals["Births"],
            locationmode="USA-states",
            colorscale="Viridis",
            colorbar_title="Births",
            colorbar_tickformat=",",
            text=state_totals["State of Residence"],
            hovertemplate="<b>%{text} (%{location})</b><br>Total Births: <b>%{z:,}</b><extra></extra>",
            marker_line_color="white",
            marker_line_width=1,
        )
    )

    fig.update_layout(
        geo=dict(
            scope="usa",
            projection=dict(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(240, 248, 255)",
            bgcolor="rgba(0,0,0,0)",
        ),
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=480,
    )
    _apply_standard_layout(fig, title="Geographic Birth Volume Across the United States", height=480)
    return fig


def create_top_bottom_chart(df: pd.DataFrame, n: int = 5) -> go.Figure:
    """
    Visual comparison of the top N and bottom N states to illustrate
    demographic scale differences for business analytics students.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "Top vs. Bottom Geographies (No Data Available)")

    state_totals = (
        df.groupby("State of Residence", as_index=False)["Births"]
        .sum()
        .sort_values(by="Births", ascending=False)
    )

    total_geos = len(state_totals)
    effective_n = min(n, total_geos // 2) if total_geos >= 4 else total_geos

    if total_geos <= 2:
        top_slice = state_totals.copy()
        top_slice["Tier"] = "Selected Geographies"
        combined = top_slice
    else:
        top_slice = state_totals.head(effective_n).copy()
        top_slice["Tier"] = f"Top {effective_n} Geographies"
        bottom_slice = state_totals.tail(effective_n).copy()
        bottom_slice["Tier"] = f"Bottom {effective_n} Geographies"
        combined = pd.concat([top_slice, bottom_slice]).sort_values(by="Births", ascending=True)

    color_map = {
        f"Top {effective_n} Geographies": "#1E3A8A",
        f"Bottom {effective_n} Geographies": "#0D9488",
        "Selected Geographies": "#1E3A8A"
    }

    fig = go.Figure()
    for tier in combined["Tier"].unique():
        tier_slice = combined[combined["Tier"] == tier]
        fig.add_trace(
            go.Bar(
                x=tier_slice["Births"],
                y=tier_slice["State of Residence"],
                orientation="h",
                name=tier,
                marker_color=color_map.get(tier, "#0284C7"),
                text=[f"{v:,}" for v in tier_slice["Births"]],
                textposition="auto",
                hovertemplate="<b>%{y}</b><br>Tier: " + tier + "<br>Births: <b>%{x:,}</b><extra></extra>",
            )
        )

    _apply_standard_layout(
        fig,
        title=f"Comparison: Highest vs. Lowest Volume Geographies",
        xaxis_title="Total Live Births (Count)",
        yaxis_title="State / Geography",
        height=420
    )
    fig.update_xaxes(rangemode="tozero", tickformat=",")
    return fig


def create_state_month_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Renders a 2D matrix heatmap showing Month (X-axis) vs State (Y-axis).
    Highlights seasonality across states.
    """
    if df.empty:
        fig = go.Figure()
        return _apply_standard_layout(fig, "Seasonal Heatmap (No Data Available)")

    pivot = (
        df.pivot_table(
            index="State of Residence",
            columns="Month",
            values="Births",
            aggfunc="sum",
            observed=True
        )
        .fillna(0)
    )

    # Reorder columns explicitly to calendar months present in selection
    cols = [m for m in CALENDAR_MONTHS if m in pivot.columns]
    pivot = pivot[cols]

    # Calculate dynamic height based on state count
    height = max(420, len(pivot) * 18 + 120)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="Teal",
            colorbar_title="Births",
            colorbar_tickformat=",",
            hovertemplate="<b>State: %{y}</b><br>Month: %{x}<br>Births: <b>%{z:,}</b><extra></extra>",
        )
    )

    _apply_standard_layout(
        fig,
        title="State-by-Month Birth Count Matrix (Heatmap)",
        xaxis_title="Month",
        yaxis_title="State of Residence",
        height=height
    )
    return fig
