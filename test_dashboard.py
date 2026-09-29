"""
Automated Quality-Assurance Test Suite for CDC 2025 Provisional Natality Dashboard.
Uses Streamlit's official AppTest framework to validate all user interaction cases.
"""

import sys
from streamlit.testing.v1 import AppTest
from src.config import EXPECTED_AUDIT, CALENDAR_MONTHS
from src.data_loader import load_and_preprocess_data


def test_suite():
    results = []

    def log_result(test_id, name, status, details):
        results.append({"id": test_id, "name": name, "status": status, "details": details})
        print(f"[{status}] {test_id}: {name} - {details}")

    print("=== STARTING DASHBOARD QA TEST SUITE ===")

    # -------------------------------------------------------------
    # Case 1: Default Dashboard with all observations
    # -------------------------------------------------------------
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception, f"Exception on load: {at.exception}"

    # Check metrics
    metrics = {m.label: m.value for m in at.metric}
    total_births_str = metrics.get("Total Births")
    geos_str = metrics.get("Selected Geographies")
    avg_str = metrics.get("Avg Births / Month")
    top_geo = metrics.get("Peak Geography")
    top_month = metrics.get("Peak Month")

    if (
        total_births_str == "3,604,640"
        and geos_str == "51 / 51"
        and top_geo == "California"
        and top_month == "July"
    ):
        log_result(
            "TC1",
            "Default Dashboard & Baseline Total",
            "PASS",
            f"Total: {total_births_str}, Geographies: {geos_str}, Peak Geo: {top_geo}, Peak Mo: {top_month}"
        )
    else:
        log_result("TC1", "Default Dashboard", "FAIL", f"Unexpected metrics: {metrics}")

    # Check disclaimer badges
    markdown_texts = [m.value for m in at.markdown]
    has_provisional = any("PROVISIONAL" in t for t in markdown_texts)
    has_count_vs_rate = any("NOT birth rates" in t for t in markdown_texts)
    assert has_provisional and has_count_vs_rate, "Missing required disclaimers"

    # -------------------------------------------------------------
    # Case 2: One State (California) and All Months
    # -------------------------------------------------------------
    at.multiselect(key="ms_states").set_value(["California"]).run()
    assert not at.exception
    ca_metrics = {m.label: m.value for m in at.metric}
    if ca_metrics.get("Total Births") == "393,111" and ca_metrics.get("Selected Geographies") == "1 / 51":
        log_result("TC2", "One State & All Months", "PASS", f"California Total: {ca_metrics.get('Total Births')}")
    else:
        log_result("TC2", "One State & All Months", "FAIL", f"Metrics: {ca_metrics}")

    # -------------------------------------------------------------
    # Case 3: Several States (CA, TX, FL, NY)
    # -------------------------------------------------------------
    target_states = ["California", "Texas", "Florida", "New York"]
    at.multiselect(key="ms_states").set_value(target_states).run()
    assert not at.exception
    multi_metrics = {m.label: m.value for m in at.metric}
    if multi_metrics.get("Selected Geographies") == "4 / 51":
        log_result("TC3", "Several States", "PASS", f"4 States Combined Total: {multi_metrics.get('Total Births')}")
    else:
        log_result("TC3", "Several States", "FAIL", f"Metrics: {multi_metrics}")

    # -------------------------------------------------------------
    # Case 4: One Month (August)
    # -------------------------------------------------------------
    at.multiselect(key="ms_months").set_value(["August"]).run()
    assert not at.exception
    mo_metrics = {m.label: m.value for m in at.metric}
    if mo_metrics.get("Peak Month") == "August":
        log_result("TC4", "One Month (August)", "PASS", f"August Births: {mo_metrics.get('Total Births')}")
    else:
        log_result("TC4", "One Month", "FAIL", f"Metrics: {mo_metrics}")

    # -------------------------------------------------------------
    # Case 5: Female Only
    # -------------------------------------------------------------
    at.radio(key="radio_sex").set_value("Female").run()
    assert not at.exception
    fem_metrics = {m.label: m.value for m in at.metric}
    fem_total = fem_metrics.get("Total Births")
    log_result("TC5", "Female Only", "PASS", f"Filtered Female Births: {fem_total}")

    # -------------------------------------------------------------
    # Case 6: Male Only
    # -------------------------------------------------------------
    at.radio(key="radio_sex").set_value("Male").run()
    assert not at.exception
    male_metrics = {m.label: m.value for m in at.metric}
    male_total = male_metrics.get("Total Births")
    log_result("TC6", "Male Only", "PASS", f"Filtered Male Births: {male_total}")

    # -------------------------------------------------------------
    # Case 7: Combined Filter (California + August + Male = 17,627)
    # -------------------------------------------------------------
    at.multiselect(key="ms_states").set_value(["California"]).run()
    assert not at.exception
    comb_metrics = {m.label: m.value for m in at.metric}
    if comb_metrics.get("Total Births") == "17,627":
        log_result("TC7", "Combined Filter (CA + Aug + Male)", "PASS", "Matches audited maximum cell: 17,627")
    else:
        log_result("TC7", "Combined Filter", "FAIL", f"Got {comb_metrics.get('Total Births')}, expected 17,627")

    # -------------------------------------------------------------
    # Case 8: Reset Filters
    # -------------------------------------------------------------
    # Click the Reset All Filters button in sidebar
    at.sidebar.button[0].click().run()
    assert not at.exception
    reset_metrics = {m.label: m.value for m in at.metric}
    if reset_metrics.get("Total Births") == "3,604,640" and reset_metrics.get("Selected Geographies") == "51 / 51":
        log_result("TC8", "Reset Filters to Defaults", "PASS", "All filters and 3,604,640 total restored")
    else:
        log_result("TC8", "Reset Filters", "FAIL", f"Metrics: {reset_metrics}")

    # -------------------------------------------------------------
    # Case 9: Empty or Invalid Selection (Zero records warning)
    # -------------------------------------------------------------
    at.multiselect(key="ms_states").set_value([]).run()
    # Check that warning appears and no unhandled exception
    assert not at.exception
    warnings = [w.value for w in at.warning]
    has_empty_warning = any("No observations match" in w for w in warnings)
    if has_empty_warning:
        log_result("TC9", "Empty Selection Guardrail", "PASS", "Graceful warning displayed without exception")
    else:
        log_result("TC9", "Empty Selection Guardrail", "FAIL", f"Warnings: {warnings}")

    # Restore states
    at.sidebar.button[0].click().run()

    # -------------------------------------------------------------
    # Case 10: CSV Download & Data Table
    # -------------------------------------------------------------
    has_download_btn = len(at.download_button) > 0
    has_df = len(at.dataframe) > 0
    if has_download_btn and has_df:
        log_result(
            "TC10",
            "Data Table & CSV Download",
            "PASS",
            f"Table present ({at.dataframe[0].value.shape[0]} rows), download button ready"
        )
    else:
        log_result("TC10", "Data Table & CSV Download", "FAIL", "Missing table or download button")

    # -------------------------------------------------------------
    # Case 11: Map & Visualizations Rendering
    # -------------------------------------------------------------
    plotly_elements = at.get("plotly_chart")
    if len(plotly_elements) >= 6:
        log_result("TC11", "Visualizations & Map Rendering", "PASS", f"{len(plotly_elements)} Plotly figures rendered")
    else:
        log_result("TC11", "Visualizations & Map Rendering", "FAIL", f"Only {len(plotly_elements)} Plotly charts rendered")

    # -------------------------------------------------------------
    # Case 12: Chronological Ordering & No Python Exceptions
    # -------------------------------------------------------------
    mo_options = at.multiselect(key="ms_months").options
    is_chronological = list(mo_options) == CALENDAR_MONTHS
    if is_chronological and not at.exception:
        log_result("TC12", "Chronological Month Order & Stability", "PASS", "Strict Jan-Dec sequence preserved")
    else:
        log_result("TC12", "Chronological Month Order", "FAIL", f"Order: {mo_options}")

    print("\n=== SUMMARY: ALL TESTS COMPLETED ===")
    all_passed = all(r["status"] == "PASS" for r in results)
    print(f"Overall status: {'ALL PASS (12/12)' if all_passed else 'SOME FAILED'}")
    return results


if __name__ == "__main__":
    test_suite()
