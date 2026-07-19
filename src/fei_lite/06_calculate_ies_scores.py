import pandas as pd
from pathlib import Path

input_path = Path("data/processed/vehicle_kpi_dataset.csv")
output_path = Path("data/processed/ies_scores.csv")
summary_path = Path("outputs/tables/ies_summary.csv")

df = pd.read_csv(input_path)

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

before_idle_median = before_df["idle_ratio"].median()

print("KPI dataset loaded")
print(f"Rows: {len(df)}")
print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")
print(f"Before fleet median idle ratio: {before_idle_median:.4f}")

before_df = before_df[[
    "vehicle",
    "idle_ratio"
]].rename(columns={
    "idle_ratio": "before_idle_ratio"
})

after_df = after_df[[
    "vehicle",
    "idle_ratio"
]].rename(columns={
    "idle_ratio": "after_idle_ratio"
})

ies_df = before_df.merge(after_df, on="vehicle", how="inner")

ies_df["before_ies"] = (
    before_idle_median / ies_df["before_idle_ratio"]
) * 100

ies_df["after_ies"] = (
    before_idle_median / ies_df["after_idle_ratio"]
) * 100

ies_df["before_ies"] = ies_df["before_ies"].clip(upper=100)
ies_df["after_ies"] = ies_df["after_ies"].clip(upper=100)

ies_df["idle_change_pct"] = (
    (ies_df["after_idle_ratio"] - ies_df["before_idle_ratio"])
    / ies_df["before_idle_ratio"]
) * 100

ies_df["ies_change"] = ies_df["after_ies"] - ies_df["before_ies"]

ies_df = ies_df.sort_values(
    "idle_change_pct",
    ascending=True
).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)

ies_df.to_csv(output_path, index=False)

summary = pd.DataFrame([
    {
        "metric": "before_fleet_median_idle_ratio",
        "value": before_idle_median
    },
    {
        "metric": "fleet_avg_before_ies",
        "value": ies_df["before_ies"].mean()
    },
    {
        "metric": "fleet_avg_after_ies",
        "value": ies_df["after_ies"].mean()
    },
    {
        "metric": "fleet_avg_ies_change",
        "value": ies_df["ies_change"].mean()
    },
    {
        "metric": "fleet_avg_idle_change_pct",
        "value": ies_df["idle_change_pct"].mean()
    },
    {
        "metric": "vehicles_idle_improved",
        "value": (ies_df["idle_change_pct"] < 0).sum()
    },
    {
        "metric": "vehicles_idle_worsened",
        "value": (ies_df["idle_change_pct"] > 0).sum()
    }
])

summary.to_csv(summary_path, index=False)

print("\nIES scores saved")
print(f"Output: {output_path}")
print(f"Summary: {summary_path}")

print("\nTop vehicles by idle reduction")
print(ies_df[[
    "vehicle",
    "before_idle_ratio",
    "after_idle_ratio",
    "idle_change_pct",
    "before_ies",
    "after_ies",
    "ies_change"
]].head())

print("\nFleet summary")
print(summary)