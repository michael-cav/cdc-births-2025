"""
Data loading, validation, and preprocessing pipeline for CDC Natality data.

Adheres to data-quality audit rules:
- Verifies exact baseline requirements (1,224 rows, 51 geographies, 12 months, 2 sexes).
- Verifies 0 missing values, 0 duplicate rows, and 3,604,640 total births.
- Adds geographic postal codes for choropleth mapping.
- Guarantees strict chronological ordering for calendar months.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st

from src.config import DATA_PATH, STATE_TO_ABBREV, CALENDAR_MONTHS, EXPECTED_AUDIT


class DataValidationError(Exception):
    """Custom exception raised when source dataset fails audit checks."""
    pass


def validate_raw_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs data quality checks against expected benchmarks.
    Returns an audit summary dictionary.
    """
    required_cols = [
        "State of Residence", "Month", "Month Code",
        "Year Code", "Sex of Infant", "Births"
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns in dataset: {missing_cols}")

    obs_count = len(df)
    geo_count = df["State of Residence"].nunique()
    month_count = df["Month Code"].nunique()
    sex_count = df["Sex of Infant"].nunique()
    missing_val_count = int(df[required_cols].isna().sum().sum())
    duplicate_count = int(df.duplicated(subset=required_cols).sum())
    total_births = int(df["Births"].sum())

    audit_results = {
        "observations": obs_count,
        "geographies": geo_count,
        "months": month_count,
        "sexes": sex_count,
        "missing": missing_val_count,
        "duplicates": duplicate_count,
        "total_births": total_births,
    }

    # Verify against expected benchmarks
    for key, expected_val in EXPECTED_AUDIT.items():
        actual_val = audit_results[key]
        if actual_val != expected_val:
            raise DataValidationError(
                f"Data audit failure for '{key}': expected {expected_val}, found {actual_val}."
            )

    return audit_results


@st.cache_data(show_spinner="Loading and validating provisional CDC natality data...")
def load_and_preprocess_data(file_path: Path = DATA_PATH) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reads the original Excel workbook, validates data integrity, and applies
    transformations required for downstream analytics and visualizations.
    
    Returns:
        Tuple of (clean_dataframe, audit_summary_dictionary)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Workbook not found at specified path: {file_path}")

    # Read the first sheet (read-only)
    df = pd.read_excel(file_path, sheet_name=0)

    # Run strict data quality audit
    audit_summary = validate_raw_data(df)

    # Ensure numeric types
    df["Month Code"] = df["Month Code"].astype(int)
    df["Year Code"] = df["Year Code"].astype(int)
    df["Births"] = df["Births"].astype(int)

    # Enforce chronological ordering on Month
    df["Month"] = pd.Categorical(df["Month"], categories=CALENDAR_MONTHS, ordered=True)

    # Map State to 2-letter postal code for choropleth map
    df["State Code"] = df["State of Residence"].map(STATE_TO_ABBREV)
    if df["State Code"].isna().any():
        unmapped = df[df["State Code"].isna()]["State of Residence"].unique().tolist()
        raise DataValidationError(f"Could not map states to postal abbreviations: {unmapped}")

    # Sort deterministically
    df = df.sort_values(by=["State of Residence", "Month Code", "Sex of Infant"]).reset_index(drop=True)

    return df, audit_summary
