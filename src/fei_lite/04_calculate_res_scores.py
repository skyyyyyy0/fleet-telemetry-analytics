from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/processed/vehicle_kpi_dataset.csv")
OUTPUT_PATH = Path("data/processed/res_scores.csv")
SUMMARY_PATH = Path("outputs/tables/res_summary.csv")

CHANGE_TOLERANCE = 1e-9


df = pd.read_csv(INPUT_PATH)

required_columns = {
    "vehicle",
    "period",
    "rpm_efficiency_ratio",
    "avg_rpm",
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

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

before_median_rpm_ratio = before_df[
    "rpm_efficiency_ratio"
].median()

if (
    pd.isna(before_median_rpm_ratio)
    or before_median_rpm_ratio <= 0
):
    raise ValueError(
        "Before RPM efficiency baseline must be positive"
    )

before_df = before_df[
    [
        "vehicle",
        "rpm_efficiency_ratio",
        "avg_rpm",
    ]
].rename(
    columns={
        "rpm_efficiency_ratio":
            "before_rpm_efficiency_ratio",
        "avg_rpm": "before_avg_rpm",
    }
)

after_df = after_df[
    [
        "vehicle",
        "rpm_efficiency_ratio",
        "avg_rpm",
    ]
].rename(
    columns={
        "rpm_efficiency_ratio":
            "after_rpm_efficiency_ratio",
        "avg_rpm": "after_avg_rpm",
    }
)

res_df = before_df.merge(
    after_df,
    on="vehicle",
    how="outer",
    validate="one_to_one",
)

res_df["valid_pair"] = (
    res_df["before_rpm_efficiency_ratio"].notna()
    & res_df["after_rpm_efficiency_ratio"].notna()
)

# Baseline-centered prototype indices.
# A value of 100 represents the fleet Before median.
res_df["before_res_raw"] = (
    res_df["before_rpm_efficiency_ratio"]
    / before_median_rpm_ratio
) * 100

res_df["after_res_raw"] = (
    res_df["after_rpm_efficiency_ratio"]
    / before_median_rpm_ratio
) * 100

# Keep capped scores temporarily for compatibility.
# Raw indices will be used later for saturation analysis.
res_df["before_res"] = (
    res_df["before_res_raw"].clip(lower=0, upper=100)
)

res_df["after_res"] = (
    res_df["after_res_raw"].clip(lower=0, upper=100)
)

before_denominator = res_df[
    "before_rpm_efficiency_ratio"
].where(
    res_df["before_rpm_efficiency_ratio"] > 0
)

res_df["rpm_efficiency_change_pct"] = (
    (
        res_df["after_rpm_efficiency_ratio"]
        - res_df["before_rpm_efficiency_ratio"]
    )
    / before_denominator
) * 100

res_df["rpm_efficiency_change_pp"] = (
    res_df["after_rpm_efficiency_ratio"]
    - res_df["before_rpm_efficiency_ratio"]
) * 100

res_df["res_raw_change"] = (
    res_df["after_res_raw"]
    - res_df["before_res_raw"]
)

res_df["res_change"] = (
    res_df["after_res"]
    - res_df["before_res"]
)


def classify_change(row):
    if not row["valid_pair"]:
        return "Missing"

    change = row["rpm_efficiency_change_pp"]

    if np.isclose(
        change,
        0,
        atol=CHANGE_TOLERANCE,
        rtol=0,
    ):
        return "Unchanged"

    if change > 0:
        return "Improved"

    return "Declined"


res_df["change_status"] = res_df.apply(
    classify_change,
    axis=1,
)

res_df = res_df.sort_values(
    "rpm_efficiency_change_pp",
    ascending=False,
    na_position="last",
).reset_index(drop=True)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

res_df.to_csv(OUTPUT_PATH, index=False)

valid_df = res_df[res_df["valid_pair"]].copy()

summary = pd.DataFrame(
    [
        {
            "metric":
                "before_fleet_median_rpm_efficiency_ratio",
            "value": before_median_rpm_ratio,
        },
        {
            "metric": "valid_vehicle_count",
            "value": len(valid_df),
        },
        {
            "metric": "missing_vehicle_count",
            "value": (~res_df["valid_pair"]).sum(),
        },
        {
            "metric": "fleet_avg_before_res",
            "value": valid_df["before_res"].mean(),
        },
        {
            "metric": "fleet_avg_after_res",
            "value": valid_df["after_res"].mean(),
        },
        {
            "metric": "fleet_avg_res_change",
            "value": valid_df["res_change"].mean(),
        },
        {
            "metric": "fleet_avg_res_raw_change",
            "value": valid_df["res_raw_change"].mean(),
        },
        {
            "metric":
                "fleet_avg_rpm_efficiency_change_pct",
            "value": valid_df[
                "rpm_efficiency_change_pct"
            ].mean(),
        },
        {
            "metric":
                "fleet_avg_rpm_efficiency_change_pp",
            "value": valid_df[
                "rpm_efficiency_change_pp"
            ].mean(),
        },
        {
            "metric": "vehicles_improved",
            "value": (
                res_df["change_status"] == "Improved"
            ).sum(),
        },
        {
            "metric": "vehicles_unchanged",
            "value": (
                res_df["change_status"] == "Unchanged"
            ).sum(),
        },
        {
            "metric": "vehicles_declined",
            "value": (
                res_df["change_status"] == "Declined"
            ).sum(),
        },
        {
            "metric": "before_score_saturation_count",
            "value": (
                valid_df["before_res_raw"] > 100
            ).sum(),
        },
        {
            "metric": "after_score_saturation_count",
            "value": (
                valid_df["after_res_raw"] > 100
            ).sum(),
        },
    ]
)

summary.to_csv(SUMMARY_PATH, index=False)

print("KPI dataset loaded")
print(f"Rows: {len(df)}")
print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")

print("\nRES scores saved")
print(f"Output: {OUTPUT_PATH}")
print(f"Summary: {SUMMARY_PATH}")

print("\nBefore fleet median RPM efficiency ratio")
print(round(before_median_rpm_ratio, 6))

print("\nFleet summary")
print(summary.to_string(index=False))

print("\nTop vehicles by RPM efficiency improvement")
print(
    res_df[
        [
            "vehicle",
            "before_rpm_efficiency_ratio",
            "after_rpm_efficiency_ratio",
            "rpm_efficiency_change_pp",
            "before_res_raw",
            "after_res_raw",
            "change_status",
        ]
    ].head()
)