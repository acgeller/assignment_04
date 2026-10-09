"""
join.py — Step 2 of the pipeline: bring the roster onto the timesheet.

The timesheet knows *who worked and how long*. The roster knows *what each
person is paid*. Neither file can produce a paycheck on its own, so the pipeline
has to combine them — and the two files have different **grains**: one row per
week-of-work versus one row per person. That is exactly what `pd.merge` is for.

The decision in this step is not *how* to merge but *which kind*. Read the
docstring before you pick `how=`.

Less scaffolding here: the steps are described, the code is yours.
"""

import pandas as pd


def merge_employees(timesheet: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    """Return the timesheet with every roster column added to each row.

    Given the (already cleaned) timesheet and the (already cleaned) roster,
    return one row **per timesheet row** with that employee's roster columns —
    `first_name`, `last_name`, `department`, `hourly_rate`, `hourly_rate_usd` —
    filled in beside the timesheet columns.

    Two rules, and both come from the same real-world situation:

    1. **Every timesheet row survives.** An `employee_id` that is not on the
       roster (a new hire HR has not entered yet, a typo by a shift lead) still
       worked those hours. Its roster columns come back as `NaN`, and Step 3 will
       label it — but if it vanishes here, the person does not get paid and
       nobody notices. So the merge keeps all rows of the *left* frame.
    2. **Rostered people who did not work do not appear.** No timesheet row, no
       paycheck. The roster is the *right* frame, and its unmatched rows are not
       wanted.

    Those two rules name the join type. Look at lesson 3-3's four examples and
    pick the `how=` that keeps everything on one side and only matches from the
    other.

    The result has every timesheet column with its original values, every
    roster column, and the same number of rows as the timesheet, in the same
    order. Match on `employee_id`, which both frames call by the same name — so
    you can use `on=` instead of `left_on=`/`right_on=`. (`how="left"` with the
    timesheet on the left, or `how="right"` with the frames swapped, both say
    "keep the timesheet's side" — pick whichever reads best to you.)
    """
   
    roster_subset = employees[["employee_id", "first_name", "last_name", "department", "hourly_rate", "hourly_rate_usd"]]
    merged = pd.merge(timesheet, roster_subset, how="left", on="employee_id")
    return merged
