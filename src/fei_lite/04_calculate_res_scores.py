import pandas as pd
from pathlib import Path

input_path = Path("data/processed/vehicle_kpi_dataset.csv")
output_path = Path("data/processed/res_scores.csv")
summary_path = Path("outputs/tables/res_summary.csv")

df = pd.read_csv(input_path)

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

before_median_rpm_ratio = before_df["rpm_efficiency_ratio"].median()

before_df = before_df[[
    "vehicle",
    "rpm_efficiency_ratio",
    "avg_rpm"
]].rename(columns={
    "rpm_efficiency_ratio": "before_rpm_efficiency_ratio",
    "avg_rpm": "before_avg_rpm"
})

after_df = after_df[[
    "vehicle",
    "rpm_efficiency_ratio",
    "avg_rpm"
]].rename(columns={
    "rpm_efficiency_ratio": "after_rpm_efficiency_ratio",
    "avg_rpm": "after_avg_rpm"
})

res_df = before_df.merge(after_df, on="vehicle", how="inner")

res_df["before_res"] = (
    res_df["before_rpm_efficiency_ratio"] / before_median_rpm_ratio
) * 100

res_df["after_res"] = (
    res_df["after_rpm_efficiency_ratio"] / before_median_rpm_ratio
) * 100

res_df["before_res"] = res_df["before_res"].clip(upper=100)
res_df["after_res"] = res_df["after_res"].clip(upper=100)

res_df["rpm_efficiency_change_pct"] = (
    (res_df["after_rpm_efficiency_ratio"] - res_df["before_rpm_efficiency_ratio"])
    / res_df["before_rpm_efficiency_ratio"]
) * 100

res_df["res_change"] = res_df["after_res"] - res_df["before_res"]

res_df = res_df.sort_values(
    "rpm_efficiency_change_pct",
    ascending=False
).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)

res_df.to_csv(output_path, index=False)

summary = pd.DataFrame([
    {"metric": "before_fleet_median_rpm_efficiency_ratio", "value": before_median_rpm_ratio},
    {"metric": "fleet_avg_before_res", "value": res_df["before_res"].mean()},
    {"metric": "fleet_avg_after_res", "value": res_df["after_res"].mean()},
    {"metric": "fleet_avg_res_change", "value": res_df["res_change"].mean()},
    {"metric": "fleet_avg_rpm_efficiency_change_pct", "value": res_df["rpm_efficiency_change_pct"].mean()},
    {"metric": "vehicles_improved", "value": (res_df["rpm_efficiency_change_pct"] > 0).sum()},
    {"metric": "vehicles_declined", "value": (res_df["rpm_efficiency_change_pct"] < 0).sum()}
])

summary.to_csv(summary_path, index=False)

print("RES scores saved")
print(f"Output: {output_path}")
print(f"Summary: {summary_path}")

print("\nBefore fleet median RPM efficiency ratio:")
print(round(before_median_rpm_ratio, 4))

print("\nTop vehicles by RPM efficiency improvement")
print(res_df[[
    "vehicle",
    "before_rpm_efficiency_ratio",
    "after_rpm_efficiency_ratio",
    "rpm_efficiency_change_pct",
    "before_res",
    "after_res",
    "res_change"
]].head())

print("\nFleet summary")
print(summary)