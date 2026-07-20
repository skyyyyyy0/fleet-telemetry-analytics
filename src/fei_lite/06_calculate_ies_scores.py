from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/processed/vehicle_kpi_dataset.csv")
OUTPUT_PATH = Path("data/processed/ies_scores.csv")
SUMMARY_PATH = Path("outputs/tables/ies_summary.csv")

CHANGE_TOLERANCE = 1e-9


df = pd.read_csv(INPUT_PATH)

required_columns = {
    "vehicle",
    "period",
    "idle_ratio",
    "idle_time_hours",
    "engine_on_time_hours",
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

if df.duplicated(["vehicle", "period"]).any():
    raise ValueError(
        "Duplicate vehicle-period rows found in KPI dataset"
    )

invalid_idle_ratio = (
    df["idle_ratio"].notna()
    & ~df["idle_ratio"].between(0, 1, inclusive="both")
)

if invalid_idle_ratio.any():
    raise ValueError(
        "idle_ratio must be between 0 and 1"
    )

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

before_idle_median = before_df["idle_ratio"].median()

if (
    pd.isna(before_idle_median)
    or before_idle_median <= 0
):
    raise ValueError(
        "Before idle-ratio baseline must be positive"
    )

before_df = before_df[
    [
        "vehicle",
        "idle_ratio",
        "idle_time_hours",
        "engine_on_time_hours",
    ]
].rename(
    columns={
        "idle_ratio": "before_idle_ratio",
        "idle_time_hours": "before_idle_time_hours",
        "engine_on_time_hours":
            "before_engine_on_time_hours",
    }
)

after_df = after_df[
    [
        "vehicle",
        "idle_ratio",
        "idle_time_hours",
        "engine_on_time_hours",
    ]
].rename(
    columns={
        "idle_ratio": "after_idle_ratio",
        "idle_time_hours": "after_idle_time_hours",
        "engine_on_time_hours":
            "after_engine_on_time_hours",
    }
)

ies_df = before_df.merge(
    after_df,
    on="vehicle",
    how="outer",
    validate="one_to_one",
)

ies_df["valid_pair"] = (
    ies_df["before_idle_ratio"].notna()
    & ies_df["after_idle_ratio"].notna()
)

# Lower idle ratio is better.
# A raw index of 100 represents the fleet Before median.
before_positive = ies_df["before_idle_ratio"].where(
    ies_df["before_idle_ratio"] > 0
)

after_positive = ies_df["after_idle_ratio"].where(
    ies_df["after_idle_ratio"] > 0
)

ies_df["before_ies_raw"] = (
    before_idle_median / before_positive
) * 100

ies_df["after_ies_raw"] = (
    before_idle_median / after_positive
) * 100

# Retain capped scores temporarily for compatibility.
# A genuine zero idle ratio is a valid perfect capped score,
# while a missing ratio remains NaN.
ies_df["before_ies"] = (
    ies_df["before_ies_raw"].clip(lower=0, upper=100)
)

ies_df["after_ies"] = (
    ies_df["after_ies_raw"].clip(lower=0, upper=100)
)

ies_df.loc[
    ies_df["before_idle_ratio"].eq(0),
    "before_ies",
] = 100

ies_df.loc[
    ies_df["after_idle_ratio"].eq(0),
    "after_ies",
] = 100

ies_df.loc[
    ies_df["before_idle_ratio"].isna(),
    "before_ies",
] = np.nan

ies_df.loc[
    ies_df["after_idle_ratio"].isna(),
    "after_ies",
] = np.nan

before_denominator = ies_df[
    "before_idle_ratio"
].where(
    ies_df["before_idle_ratio"] > 0
)

ies_df["idle_change_pct"] = (
    (
        ies_df["after_idle_ratio"]
        - ies_df["before_idle_ratio"]
    )
    / before_denominator
) * 100

ies_df["idle_change_pp"] = (
    ies_df["after_idle_ratio"]
    - ies_df["before_idle_ratio"]
) * 100

ies_df["ies_raw_change"] = (
    ies_df["after_ies_raw"]
    - ies_df["before_ies_raw"]
)

ies_df["ies_change"] = (
    ies_df["after_ies"]
    - ies_df["before_ies"]
)


def classify_change(row):
    if not row["valid_pair"]:
        return "Missing"

    change = row["idle_change_pp"]

    if np.isclose(
        change,
        0,
        atol=CHANGE_TOLERANCE,
        rtol=0,
    ):
        return "Unchanged"

    # Lower idle ratio means improvement.
    if change < 0:
        return "Improved"

    return "Declined"


ies_df["change_status"] = ies_df.apply(
    classify_change,
    axis=1,
)

ies_df = ies_df.sort_values(
    "idle_change_pp",
    ascending=True,
    na_position="last",
).reset_index(drop=True)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

ies_df.to_csv(OUTPUT_PATH, index=False)

valid_df = ies_df[ies_df["valid_pair"]].copy()

before_saturated = (
    valid_df["before_ies_raw"].gt(100)
    | valid_df["before_idle_ratio"].eq(0)
)

after_saturated = (
    valid_df["after_ies_raw"].gt(100)
    | valid_df["after_idle_ratio"].eq(0)
)

summary = pd.DataFrame(
    [
        {
            "metric": "before_fleet_median_idle_ratio",
            "value": before_idle_median,
        },
        {
            "metric": "valid_vehicle_count",
            "value": len(valid_df),
        },
        {
            "metric": "missing_vehicle_count",
            "value": (~ies_df["valid_pair"]).sum(),
        },
        {
            "metric": "fleet_avg_before_idle_ratio",
            "value": valid_df["before_idle_ratio"].mean(),
        },
        {
            "metric": "fleet_avg_after_idle_ratio",
            "value": valid_df["after_idle_ratio"].mean(),
        },
        {
            "metric": "fleet_avg_idle_change_pp",
            "value": valid_df["idle_change_pp"].mean(),
        },
        {
            "metric": "fleet_avg_idle_change_pct",
            "value": valid_df["idle_change_pct"].mean(),
        },
        {
            "metric": "fleet_avg_before_ies",
            "value": valid_df["before_ies"].mean(),
        },
        {
            "metric": "fleet_avg_after_ies",
            "value": valid_df["after_ies"].mean(),
        },
        {
            "metric": "fleet_avg_ies_change",
            "value": valid_df["ies_change"].mean(),
        },
        {
            "metric": "fleet_avg_ies_raw_change",
            "value": valid_df["ies_raw_change"].mean(),
        },
        {
            "metric": "vehicles_improved",
            "value": (
                ies_df["change_status"] == "Improved"
            ).sum(),
        },
        {
            "metric": "vehicles_unchanged",
            "value": (
                ies_df["change_status"] == "Unchanged"
            ).sum(),
        },
        {
            "metric": "vehicles_declined",
            "value": (
                ies_df["change_status"] == "Declined"
            ).sum(),
        },
        {
            "metric": "before_zero_idle_vehicle_count",
            "value": valid_df[
                "before_idle_ratio"
            ].eq(0).sum(),
        },
        {
            "metric": "after_zero_idle_vehicle_count",
            "value": valid_df[
                "after_idle_ratio"
            ].eq(0).sum(),
        },
        {
            "metric": "before_score_saturation_count",
            "value": before_saturated.sum(),
        },
        {
            "metric": "after_score_saturation_count",
            "value": after_saturated.sum(),
        },
    ]
)

summary.to_csv(SUMMARY_PATH, index=False)

print("KPI dataset loaded")
print(f"Rows: {len(df)}")
print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")

print("\nIES scores saved")
print(f"Output: {OUTPUT_PATH}")
print(f"Summary: {SUMMARY_PATH}")

print("\nBefore fleet median idle ratio")
print(round(before_idle_median, 6))

print("\nFleet summary")
print(summary.to_string(index=False))

print("\nTop vehicles by idle reduction")
print(
    ies_df[
        [
            "vehicle",
            "before_idle_ratio",
            "after_idle_ratio",
            "idle_change_pp",
            "before_ies_raw",
            "after_ies_raw",
            "change_status",
        ]
    ].head()
)