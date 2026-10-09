"""
compute.py — Step 3 of the pipeline: pay, labels, and the file the provider wants.

Two element functions that need **two** values from a row, two DataFrame
functions that run them across every row with `DataFrame.apply(..., axis=1)`,
the function that chains all three steps into one call, and the export that
reshapes the result for the online payroll provider.

No walkthrough this time. You have `clean.py` and `join.py` beside you, the
docstrings say what each function must return, and `tests/test_unit.py` and
`tests/test_pipeline.py` say exactly how they will be checked.
"""

import pandas as pd

from .clean import add_hourly_rate, add_hours_worked
from .join import merge_employees

OVERTIME_THRESHOLD = 40.0   # weekly hours above this are paid at time-and-a-half
OVERTIME_MULTIPLIER = 1.5


def calc_gross_pay(hours: float, rate: float) -> float:
    """Gross pay for one employee-week, rounded to cents.

    Up to 40 hours at `rate`; every hour above 40 at `rate * 1.5`. A missing rate
    (`NaN`, because the employee was not on the roster) or missing hours pays
    `0.0` — the row is flagged elsewhere, it is not this function's job to crash.

    Examples:

        calc_gross_pay(38.5, 18.5)   ->  712.25
        calc_gross_pay(42.0, 19.0)   ->  817.0      # 40*19 + 2*19*1.5
        calc_gross_pay(0.75, 17.0)   ->  12.75
        calc_gross_pay(20.0, float("nan"))  ->  0.0
    """
    if pd.isna(hours) or pd.isna(rate):
        return 0.0
    if hours > OVERTIME_THRESHOLD:
        pay = OVERTIME_THRESHOLD * rate + (hours - OVERTIME_THRESHOLD) * rate * OVERTIME_MULTIPLIER
    else:
        pay = hours * rate
    return round(pay, 2)

def classify_pay(hours: float, rate: float) -> str:
    """One word the office manager can filter on: what kind of pay row is this?

        "unmatched"   the rate is missing -> employee_id was not on the roster
        "overtime"    more than 40 hours
        "regular"     everything else

    Check for unmatched *first*: an unknown employee with 45 hours is still
    unmatched, not overtime.
    """
    if pd.isna(hours) or pd.isna(rate):
        return "unmatched"
    if hours > OVERTIME_THRESHOLD:
        return "overtime"
    return "regular"


def add_gross_pay(payroll: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with one new column, `gross_pay`: `calc_gross_pay` for every row.

    The function needs two values from the same row, so this is `DataFrame.apply`
    with `axis=1`, and a lambda that unpacks the row:

        lambda row: calc_gross_pay(row["hours_worked"], row["hourly_rate_usd"])
    """
    out = payroll.copy()
    out["gross_pay"] = out.apply(
        lambda row: calc_gross_pay(row["hours_worked"], row["hourly_rate_usd"]), axis=1
    )
    return out


def add_pay_type(payroll: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with one new column, `pay_type`: `classify_pay` for every row."""
    out = payroll.copy()
    out["pay_type"] = out.apply(
        lambda row: classify_pay(row["hours_worked"], row["hourly_rate_usd"]), axis=1
    )
    return out


def build_payroll(timesheet: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    """The whole pipeline in one call: raw timesheet + raw roster -> payroll table.

    Clean both frames (Step 1), merge them (Step 2), then add `gross_pay` and
    `pay_type` (Step 3). Every column that went in comes out, plus the four the
    pipeline computes (`hours_worked`, `hourly_rate_usd`, `gross_pay`, `pay_type`)
    and the roster's columns — one row per timesheet row.
    """
    timesheet = add_hours_worked(timesheet)
    employees = add_hourly_rate(employees)
    payroll = merge_employees(timesheet, employees)
    payroll = add_gross_pay(payroll)
    payroll = add_pay_type(payroll)
    return payroll


def payroll_export(payroll: pd.DataFrame) -> pd.DataFrame:
    """The file the online payroll provider imports — a NEW frame, not a renamed one.

    Exactly these columns, in this order, with these names:

        payrolldate, employeeid, hours, rate, total

    taken from `payroll_date`, `employee_id`, `hours_worked`, `hourly_rate_usd`
    and `gross_pay`. Only rows the provider can pay: `pay_type != "unmatched"`
    (the provider rejects an ID it does not know, and the manager fixes those
    rows in the app before re-exporting).

    Build it as a new DataFrame from the columns you want — do not rename the
    pipeline's columns. The pipeline table keeps its lineage; the export is a
    view of it shaped for someone else's system.
    """
    export = payroll[payroll["pay_type"] != "unmatched"].copy()
    export = export[["payroll_date", "employee_id", "hours_worked", "hourly_rate_usd", "gross_pay"]]
    export.columns = ["payrolldate", "employeeid", "hours", "rate", "total"]
    return export
