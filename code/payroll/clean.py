"""
clean.py — Step 1 of the pipeline: turn text into numbers, one value at a time.

Two element functions that each read one messy string and return one number, and
two DataFrame functions that use `Series.apply` to run them down a whole column
and store the result in a **new** column.

The lineage rule, which every step of this pipeline follows:

    A pipeline function takes a DataFrame and returns a WIDER copy of it.
    It never changes a value it was given, never removes a column, never renames
    one, and never modifies the frame the caller passed in.

So `"38h 30m"` stays in `hours`, and `38.5` goes in `hours_worked` beside it. An
auditor reading the payroll table can see both — which is the point.

This step is walked through line by line in each docstring. The next two steps
give you less.
"""

import pandas as pd


def parse_hours(value) -> float:
    """Read a weekly-hours string the way a shift lead typed it; return a float.

    Examples:

        parse_hours("38h 30m")   ->  38.5
        parse_hours("42h")       ->  42.0
        parse_hours("45m")       ->  0.75
        parse_hours("24.5")      ->  24.5
        parse_hours("")          ->  0.0      # unreadable -> zero, never a crash
        parse_hours(None)        ->  0.0

    How to build it:

    - Guard first: if `value` is not a string, return `float(value)` if it is a
      number and `0.0` if it is `None`/missing. (`pd.isna(value)` is the test for
      missing.)
    - Strip whitespace. If what is left is empty, return `0.0`.
    - The decimal form has no letters: if `"h"` and `"m"` are both absent, try
      `float(text)`; a `ValueError` means unreadable, so return `0.0`.
    - Otherwise start `hours = 0.0`, then look at each word from `text.split()`:
      a word ending in `"h"` adds `float(word[:-1])`, a word ending in `"m"` adds
      `float(word[:-1]) / 60`. Wrap the arithmetic in `try/except ValueError`
      and return `0.0` if anything inside a word is not a number.
    - The mistake people make: forgetting the `/ 60`. `"45m"` is three quarters
      of an hour, not 45 hours, and `test_parse_hours` will tell you.
    """
    if not isinstance(value, str):
        if pd.isna(value):
            return 0.0
        else:
            return float(value)
    value = value.strip().lower()
    if not value:
        return 0.0

    # Decimal form: no letters at all
    if "h" not in value and "m" not in value:
        try:
            return float(value)
        except ValueError:
            return 0.0

    # "38h 30m" form: one word per unit
    hours = 0.0
    try:
        for word in value.split():
            if word.endswith("h"):
                hours += float(word[:-1])
            elif word.endswith("m"):
                hours += float(word[:-1]) / 60
    except ValueError:
        return 0.0
    return hours


def clean_currency(value) -> float:
    """Read a dollar amount as HR typed it; return it as a float.

    Examples:

        clean_currency("$18.50")     ->  18.5
        clean_currency("17.75")      ->  17.75
        clean_currency(" $1,020.00") ->  1020.0
        clean_currency("")           ->  0.0      # unreadable -> zero
        clean_currency(None)         ->  0.0

    How to build it:

    - Same guard as `parse_hours`: not a string -> `float(value)` for a number,
      `0.0` for missing.
    - Remove the `$` and any `,` with `.replace()`, strip whitespace, then
      `float()` inside a `try/except ValueError` that returns `0.0`.
    - You wrote this function in Assignment 02. It is the same function. That
      is not an accident — cleaning currency is something every pipeline does.
    """
    if not isinstance(value, str):
        if pd.isna(value):
            return 0.0
        else:
            return float(value)
    value = value.replace("$", "").replace(",", "").strip()
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def add_hours_worked(timesheet: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the timesheet with one new column, `hours_worked` (float).

    `hours_worked` is `parse_hours` applied to every value in `hours`. The `hours`
    column itself is untouched — the text the shift lead typed stays in the table.

    How to build it:

    - `out = timesheet.copy()` — never modify the frame you were handed.
    - `out["hours_worked"] = out["hours"].apply(parse_hours)` — `Series.apply`
      calls your function once per value and hands back a Series of the results,
      in the same order, ready to be stored as a column.
    - `return out`. Three lines. Every pipeline step in this assignment has this
      shape: copy, add a column, return.
    """
    out = timesheet.copy()
    out["hours_worked"] = out["hours"].apply(parse_hours)
    return out


def add_hourly_rate(employees: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the roster with one new column, `hourly_rate_usd` (float).

    `hourly_rate_usd` is `clean_currency` applied to every value in
    `hourly_rate`. `hourly_rate` stays exactly as HR typed it.

    How to build it: the same three lines as `add_hours_worked`, with the other
    function and the other column names.
    """
    out = employees.copy()
    out["hourly_rate_usd"] = out["hourly_rate"].apply(clean_currency)
    return out


if __name__ == "__main__":
    # Try the parser here with the debugger — the tests will not stop at breakpoints.
    for sample in ("38h 30m", "42h", "45m", "24.5", "", "forty"):
        print(repr(sample), "->", parse_hours(sample))
    print(clean_currency("$1,020.00"))
