"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st
import pandas as pd

from payroll.extract import load_employees, load_timesheet
from payroll.clean import add_hourly_rate, add_hours_worked, clean_currency, parse_hours
from payroll.join import merge_employees
from payroll.compute import build_payroll, payroll_export

st.title("Salt City Coffee — Weekly Payroll")

st.metric("Roster size", len(load_employees()), help="Number of employees in the roster.")
st.file_uploader("Upload the week's timesheet", type="csv", key="timesheet")

if st.session_state.timesheet is not None:

    timesheet = load_timesheet(st.session_state.timesheet)
    payroll = build_payroll(timesheet, load_employees())

    st.subheader(f"Pay period ending {payroll['payroll_date'].iloc[0]}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total hours", f"{payroll['hours_worked'].sum():.2f}")
    col2.metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
    col3.metric("Unmatched IDs", len(payroll[payroll["pay_type"] == "unmatched"]))
    col4.metric("Overtime rows", len(payroll[payroll["pay_type"] == "overtime"]))

    unmatched_ids = payroll.loc[payroll["pay_type"] == "unmatched", "employee_id"].unique()
    if len(unmatched_ids) > 0:
        st.warning(f"Unmatched employee IDs: {', '.join(unmatched_ids)}")
    else:
        st.success("All employee IDs matched.")

    st.dataframe(payroll)

    csv_export = payroll_export(payroll).to_csv(index=False)
    st.download_button(
        label="Download payroll CSV",
        data=csv_export,
        file_name="payroll_export.csv",
        mime="text/csv",
        key="download"
    )