import pandas as pd
import numpy as np
from pathlib import Path

input_path = Path("data/processed/vehicle_kpi_dataset.csv")
output_path = Path("data/processed/dss_scores.csv")
summary_path = Path("outputs/tables/dss_summary.csv")

df = pd.read_csv(input_path)

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

def add_driving_risk_metrics(data):
    data = data.copy()

    data["total_driving_events"] = (
        data["harsh_braking_count"]
        + data["side_accel_count"]
    )

    data["driving_events_per_100km"] = np.where(
        data["distance_km"] > 0,
        (data["total_driving_events"] / data["distance_km"]) * 100,
        np.nan
    )

    return data

before_df = add_driving_risk_metrics(before_df)
after_df = add_driving_risk_metrics(after_df)

before_risk_median = before_df.loc[
    before_df["driving_events_per_100km"] > 0,
    "driving_events_per_100km"
].median()

print("KPI dataset loaded")
print(f"Rows: {len(df)}")
print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")
print(f"Before fleet median driving events per 100km: {before_risk_median:.4f}")

before_df = before_df[[
    "vehicle",
    "distance_km",
    "harsh_braking_count",
    "side_accel_count",
    "total_driving_events",
    "driving_events_per_100km"
]].rename(columns={
    "distance_km": "before_distance_km",
    "harsh_braking_count": "before_harsh_braking_count",
    "side_accel_count": "before_side_accel_count",
    "total_driving_events": "before_total_driving_events",
    "driving_events_per_100km": "before_driving_events_per_100km"
})

after_df = after_df[[
    "vehicle",
    "distance_km",
    "harsh_braking_count",
    "side_accel_count",
    "total_driving_events",
    "driving_events_per_100km"
]].rename(columns={
    "distance_km": "after_distance_km",
    "harsh_braking_count": "after_harsh_braking_count",
    "side_accel_count": "after_side_accel_count",
    "total_driving_events": "after_total_driving_events",
    "driving_events_per_100km": "after_driving_events_per_100km"
})

dss_df = before_df.merge(after_df, on="vehicle", how="inner")

dss_df["before_dss_raw"] = np.where(
    dss_df["before_driving_events_per_100km"] > 0,
    (before_risk_median / dss_df["before_driving_events_per_100km"]) * 100,
    np.nan
)

dss_df["after_dss_raw"] = np.where(
    dss_df["after_driving_events_per_100km"] > 0,
    (before_risk_median / dss_df["after_driving_events_per_100km"]) * 100,
    np.nan
)

dss_df["before_dss"] = dss_df["before_dss_raw"].clip(upper=100)
dss_df["after_dss"] = dss_df["after_dss_raw"].clip(upper=100)

dss_df["driving_risk_change_pct"] = np.where(
    dss_df["before_driving_events_per_100km"] > 0,
    (
        dss_df["after_driving_events_per_100km"]
        - dss_df["before_driving_events_per_100km"]
    )
    / dss_df["before_driving_events_per_100km"] * 100,
    np.nan
)

dss_df["dss_change"] = dss_df["after_dss"] - dss_df["before_dss"]

dss_df = dss_df.sort_values(
    "driving_risk_change_pct",
    ascending=True
).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)

dss_df.to_csv(output_path, index=False)

valid_df = dss_df.dropna(subset=["before_dss", "after_dss"])

summary = pd.DataFrame([
    {
        "metric": "before_fleet_median_driving_events_per_100km",
        "value": before_risk_median
    },
    {
        "metric": "fleet_avg_before_dss",
        "value": valid_df["before_dss"].mean()
    },
    {
        "metric": "fleet_avg_after_dss",
        "value": valid_df["after_dss"].mean()
    },
    {
        "metric": "fleet_avg_dss_change",
        "value": valid_df["dss_change"].mean()
    },
    {
        "metric": "fleet_avg_driving_risk_change_pct",
        "value": valid_df["driving_risk_change_pct"].mean()
    },
    {
        "metric": "vehicles_smoothness_improved",
        "value": (valid_df["driving_risk_change_pct"] < 0).sum()
    },
    {
        "metric": "vehicles_smoothness_worsened",
        "value": (valid_df["driving_risk_change_pct"] > 0).sum()
    }
])

summary.to_csv(summary_path, index=False)

print("\nDSS scores saved")
print(f"Output: {output_path}")
print(f"Summary: {summary_path}")

print("\nFleet summary")
print(summary)

print("\nTop vehicles by driving smoothness improvement")
print(dss_df[[
    "vehicle",
    "before_driving_events_per_100km",
    "after_driving_events_per_100km",
    "driving_risk_change_pct",
    "before_dss",
    "after_dss",
    "dss_change"
]].head())