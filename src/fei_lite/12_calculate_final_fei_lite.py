import pandas as pd
from pathlib import Path

fes_path = Path("data/processed/fes_scores.csv")
res_path = Path("data/processed/res_scores.csv")
ies_path = Path("data/processed/ies_scores.csv")
dss_path = Path("data/processed/dss_scores.csv")

output_path = Path("data/processed/vehicle_fei_scores.csv")
summary_path = Path("outputs/tables/fei_lite_summary.csv")

fes_df = pd.read_csv(fes_path)
res_df = pd.read_csv(res_path)
ies_df = pd.read_csv(ies_path)
dss_df = pd.read_csv(dss_path)

fes_df = fes_df[[
    "vehicle",
    "before_fes",
    "after_fes",
    "fes_change"
]]

res_df = res_df[[
    "vehicle",
    "before_res",
    "after_res",
    "res_change"
]]

ies_df = ies_df[[
    "vehicle",
    "before_ies",
    "after_ies",
    "ies_change"
]]

dss_df = dss_df[[
    "vehicle",
    "before_dss",
    "after_dss",
    "dss_change"
]]

fei_df = (
    fes_df
    .merge(res_df, on="vehicle", how="inner")
    .merge(ies_df, on="vehicle", how="inner")
    .merge(dss_df, on="vehicle", how="inner")
)

score_columns = [
    "before_fes",
    "after_fes",
    "before_res",
    "after_res",
    "before_ies",
    "after_ies",
    "before_dss",
    "after_dss"
]

fei_df[score_columns] = fei_df[score_columns].fillna(100)

fei_df["before_fei_lite"] = (
    0.50 * fei_df["before_fes"]
    + 0.20 * fei_df["before_res"]
    + 0.20 * fei_df["before_ies"]
    + 0.10 * fei_df["before_dss"]
)

fei_df["after_fei_lite"] = (
    0.50 * fei_df["after_fes"]
    + 0.20 * fei_df["after_res"]
    + 0.20 * fei_df["after_ies"]
    + 0.10 * fei_df["after_dss"]
)

fei_df["fei_change"] = (
    fei_df["after_fei_lite"]
    - fei_df["before_fei_lite"]
)

fei_df["fei_change_pct"] = (
    fei_df["fei_change"]
    / fei_df["before_fei_lite"]
) * 100

fei_df["improved"] = fei_df["fei_change"] > 0

fei_df = fei_df.sort_values(
    "after_fei_lite",
    ascending=False
).reset_index(drop=True)

fei_df["rank"] = (
    fei_df["after_fei_lite"]
    .rank(ascending=False, method="dense")
    .astype("Int64")
)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)

fei_df.to_csv(output_path, index=False)

summary = pd.DataFrame([
    {
        "metric": "fleet_avg_before_fei_lite",
        "value": fei_df["before_fei_lite"].mean()
    },
    {
        "metric": "fleet_avg_after_fei_lite",
        "value": fei_df["after_fei_lite"].mean()
    },
    {
        "metric": "fleet_avg_fei_change",
        "value": fei_df["fei_change"].mean()
    },
    {
        "metric": "fleet_avg_fei_change_pct",
        "value": fei_df["fei_change_pct"].mean()
    },
    {
        "metric": "vehicles_improved",
        "value": fei_df["improved"].sum()
    },
    {
        "metric": "vehicles_declined",
        "value": (~fei_df["improved"]).sum()
    },
    {
        "metric": "top_vehicle",
        "value": fei_df.iloc[0]["vehicle"]
    },
    {
        "metric": "top_vehicle_after_fei_lite",
        "value": fei_df.iloc[0]["after_fei_lite"]
    },
    {
        "metric": "bottom_vehicle",
        "value": fei_df.iloc[-1]["vehicle"]
    },
    {
        "metric": "bottom_vehicle_after_fei_lite",
        "value": fei_df.iloc[-1]["after_fei_lite"]
    }
])

summary.to_csv(summary_path, index=False)

print("Final FEI-Lite scores saved")
print(f"Output: {output_path}")
print(f"Summary: {summary_path}")

print("\nFleet Summary")
print(summary)

print("\nVehicle Ranking")
print(fei_df[[
    "rank",
    "vehicle",
    "before_fei_lite",
    "after_fei_lite",
    "fei_change",
    "fei_change_pct"
]])