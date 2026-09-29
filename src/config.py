"""
Configuration and constants for the 2025 CDC Provisional Natality Dashboard.

Designed for undergraduate business analytics students.
Provides standardized mappings, pedagogical disclaimers, and UI constants.
"""

from pathlib import Path

# Base Paths (works across Windows, macOS, Linux, and Streamlit Community Cloud)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "Provisional_Natality_2025_CDC.xlsx"

# Page Configuration
PAGE_TITLE = "Provisional 2025 CDC Natality Dashboard"
PAGE_ICON = "👶"
LAYOUT = "wide"

# Source & Pedagogical Disclaimers
SOURCE_ATTRIBUTION = "Source: Centers for Disease Control and Prevention (CDC) National Center for Health Statistics (NCHS) - Provisional Natality Data (2025)."
PROVISIONAL_NOTICE = "⚠️ Notice: These data are PROVISIONAL and subject to ongoing validation and revision by the CDC."
COUNT_VS_RATE_NOTICE = "📌 Important Analytical Note: The figures displayed are discrete live birth counts, NOT birth rates. Differences across states primarily reflect population size rather than fertility behavior."

# Complete 51 Geographies (50 States + District of Columbia) to Postal Abbreviations
STATE_TO_ABBREV = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

# Ordered Calendar Months (Preserves strict chronological order)
CALENDAR_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Expected Dataset Audit Benchmarks
EXPECTED_AUDIT = {
    "observations": 1224,
    "geographies": 51,
    "months": 12,
    "sexes": 2,
    "missing": 0,
    "duplicates": 0,
    "total_births": 3604640
}

# Color Tokens (High-contrast, accessible)
COLORS = {
    "primary": "#1E3A8A",      # Deep Navy Blue
    "secondary": "#0284C7",    # Sky Blue
    "female": "#D946EF",       # Accessible Magenta/Fuchsia
    "male": "#0284C7",         # Accessible Blue
    "neutral_dark": "#1E293B", # Dark Slate
    "neutral_light": "#F8FAFC",# Clean Off-White
    "accent": "#0D9488",       # Teal
    "background_card": "#FFFFFF",
}
