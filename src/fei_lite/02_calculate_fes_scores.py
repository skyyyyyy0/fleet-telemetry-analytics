from pathlib import Path

import numpy as np
import pandas as pd


input_path = Path(
    "data/processed/vehicle_kpi_dataset.csv"
)
output_path = Path(
    "data/processed/fes_scores.csv"
)
summary_path = Path(
    "outputs/tables/fes_summary.csv"
)
class_summary_path = Path(
    "outputs/tables/fes_class_summary.csv"
)

CHANGE_TOLERANCE_PCT = 1e-9


def get_vehicle_class(vehicle_name):
    vehicle_name = str(vehicle_name).strip()

    if vehicle_name.startswith("HDV_"):
        return "Heavy-Duty"

    if vehicle_name.startswith("LDV_"):
        return "Light-Duty"

    return "Unknown"


df = pd.read_csv(input_path)

print("KPI dataset loaded")
print(f"Rows: {len(df)}")

if df.duplicated(["vehicle", "period"]).any():
    raise ValueError(
        "Duplicate vehicle-period rows were detected"
    )

df["vehicle_class"] = df["vehicle"].apply(
    get_vehicle_class
)

before_df = df[
    df["period"] == "before"
].copy()

after_df = df[
    df["period"] == "after"
].copy()

print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")


# The Before period is used as the fixed reference
# so that Before and After scores are comparable.
before_baseline = (
    before_df
    .groupby(
        "vehicle_class",
        as_index=False,
    )["fuel_efficiency_km_l"]
    .median()
    .rename(
        columns={
            "fuel_efficiency_km_l":
                "class_before_median_fe"
        }
    )
)


before_df = before_df[
    [
        "vehicle",
        "vehicle_class",
        "fuel_efficiency_km_l",
    ]
].rename(
    columns={
        "fuel_efficiency_km_l":
            "before_fuel_efficiency_km_l"
    }
)

after_df = after_df[
    [
        "vehicle",
        "vehicle_class",
        "fuel_efficiency_km_l",
    ]
].rename(
    columns={
        "fuel_efficiency_km_l":
            "after_fuel_efficiency_km_l"
    }
)


fes_df = before_df.merge(
    after_df,
    on=["vehicle", "vehicle_class"],
    how="outer",
    validate="one_to_one",
)

fes_df = fes_df.merge(
    before_baseline,
    on="vehicle_class",
    how="left",
    validate="many_to_one",
)


valid_baseline = fes_df[
    "class_before_median_fe"
].gt(0)

fes_df["before_fes_raw"] = np.where(
    valid_baseline
    & fes_df[
        "before_fuel_efficiency_km_l"
    ].notna(),
    (
        fes_df[
            "before_fuel_efficiency_km_l"
        ]
        / fes_df["class_before_median_fe"]
    ) * 100,
    np.nan,
)

fes_df["after_fes_raw"] = np.where(
    valid_baseline
    & fes_df[
        "after_fuel_efficiency_km_l"
    ].notna(),
    (
        fes_df[
            "after_fuel_efficiency_km_l"
        ]
        / fes_df["class_before_median_fe"]
    ) * 100,
    np.nan,
)


# Keep raw scores for saturation analysis.
# Capped scores remain the current FEI-Lite inputs.
fes_df["before_fes"] = fes_df[
    "before_fes_raw"
].clip(upper=100)

fes_df["after_fes"] = fes_df[
    "after_fes_raw"
].clip(upper=100)


fes_df["fuel_efficiency_change_pct"] = np.where(
    fes_df[
        "before_fuel_efficiency_km_l"
    ].gt(0)
    & fes_df[
        "after_fuel_efficiency_km_l"
    ].notna(),
    (
        (
            fes_df[
                "after_fuel_efficiency_km_l"
            ]
            - fes_df[
                "before_fuel_efficiency_km_l"
            ]
        )
        / fes_df[
            "before_fuel_efficiency_km_l"
        ]
    ) * 100,
    np.nan,
)

fes_df["fes_change"] = (
    fes_df["after_fes"]
    - fes_df["before_fes"]
)

fes_df["valid_pair"] = (
    fes_df["before_fes"].notna()
    & fes_df["after_fes"].notna()
)

change = fes_df[
    "fuel_efficiency_change_pct"
]

fes_df["change_status"] = np.select(
    [
        change.isna(),
        change.abs().le(
            CHANGE_TOLERANCE_PCT
        ),
        change.gt(
            CHANGE_TOLERANCE_PCT
        ),
        change.lt(
            -CHANGE_TOLERANCE_PCT
        ),
    ],
    [
        "Missing",
        "Unchanged",
        "Improved",
        "Declined",
    ],
    default="Missing",
)


fes_df = fes_df.sort_values(
    "fuel_efficiency_change_pct",
    ascending=False,
    na_position="last",
).reset_index(drop=True)


output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

fes_df.to_csv(
    output_path,
    index=False,
)


class_summary = (
    fes_df
    .groupby(
        "vehicle_class",
        as_index=False,
    )
    .agg(
        vehicle_count=(
            "vehicle",
            "count",
        ),
        valid_vehicle_count=(
            "valid_pair",
            "sum",
        ),
        class_before_median_fe=(
            "class_before_median_fe",
            "first",
        ),
        avg_before_fe=(
            "before_fuel_efficiency_km_l",
            "mean",
        ),
        avg_after_fe=(
            "after_fuel_efficiency_km_l",
            "mean",
        ),
        avg_before_fes=(
            "before_fes",
            "mean",
        ),
        avg_after_fes=(
            "after_fes",
            "mean",
        ),
        avg_fes_change=(
            "fes_change",
            "mean",
        ),
        avg_fe_change_pct=(
            "fuel_efficiency_change_pct",
            "mean",
        ),
    )
)

class_summary.to_csv(
    class_summary_path,
    index=False,
)


paired_df = fes_df[
    fes_df["valid_pair"]
].copy()

summary = pd.DataFrame(
    [
        {
            "metric": "valid_vehicle_count",
            "value": len(paired_df),
        },
        {
            "metric": "missing_vehicle_count",
            "value": (
                len(fes_df) - len(paired_df)
            ),
        },
        {
            "metric": "fleet_avg_before_fes",
            "value": paired_df[
                "before_fes"
            ].mean(),
        },
        {
            "metric": "fleet_avg_after_fes",
            "value": paired_df[
                "after_fes"
            ].mean(),
        },
        {
            "metric": "fleet_avg_fes_change",
            "value": paired_df[
                "fes_change"
            ].mean(),
        },
        {
            "metric":
                "fleet_avg_fuel_efficiency_change_pct",
            "value": paired_df[
                "fuel_efficiency_change_pct"
            ].mean(),
        },
        {
            "metric": "vehicles_improved",
            "value": (
                fes_df["change_status"]
                == "Improved"
            ).sum(),
        },
        {
            "metric": "vehicles_unchanged",
            "value": (
                fes_df["change_status"]
                == "Unchanged"
            ).sum(),
        },
        {
            "metric": "vehicles_declined",
            "value": (
                fes_df["change_status"]
                == "Declined"
            ).sum(),
        },
        {
            "metric": "heavy_duty_vehicle_count",
            "value": (
                fes_df["vehicle_class"]
                == "Heavy-Duty"
            ).sum(),
        },
        {
            "metric": "light_duty_vehicle_count",
            "value": (
                fes_df["vehicle_class"]
                == "Light-Duty"
            ).sum(),
        },
    ]
)

summary.to_csv(
    summary_path,
    index=False,
)


print("\nFES scores saved")
print(f"Output: {output_path}")
print(f"Summary: {summary_path}")
print(f"Class summary: {class_summary_path}")

print("\nClass baseline")
print(before_baseline)

print("\nClass summary")
print(class_summary)

print("\nFleet summary")
print(summary)

print("\nTop vehicles by fuel efficiency improvement")
print(
    fes_df[
        [
            "vehicle",
            "vehicle_class",
            "before_fuel_efficiency_km_l",
            "after_fuel_efficiency_km_l",
            "fuel_efficiency_change_pct",
            "before_fes",
            "after_fes",
            "fes_change",
            "change_status",
        ]
    ].head()
)