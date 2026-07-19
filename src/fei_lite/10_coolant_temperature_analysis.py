import pandas as pd
from pathlib import Path

before_path = Path("data/processed/before_clean_dataset.csv")
after_path = Path("data/processed/after_clean_dataset.csv")

output_path = Path("outputs/tables/coolant_temperature_summary.csv")
fleet_output_path = Path("outputs/tables/coolant_temperature_fleet_summary.csv")

before_df = pd.read_csv(before_path)
after_df = pd.read_csv(after_path)

print("Loading datasets")
print(f"Before rows: {len(before_df)}")
print(f"After rows : {len(after_df)}")

before_temp = before_df[
    before_df["signal"] == "coolant_temp"
].copy()

after_temp = after_df[
    after_df["signal"] == "coolant_temp"
].copy()

print("\nCoolant temperature records")
print(f"Before: {len(before_temp)}")
print(f"After : {len(after_temp)}")

before_summary = (
    before_temp
    .groupby("vehicle")["data"]
    .mean()
    .reset_index()
)

before_summary.columns = [
    "vehicle",
    "before_avg_coolant_temp"
]

after_summary = (
    after_temp
    .groupby("vehicle")["data"]
    .mean()
    .reset_index()
)

after_summary.columns = [
    "vehicle",
    "after_avg_coolant_temp"
]

summary = before_summary.merge(
    after_summary,
    on="vehicle",
    how="inner"
)

summary["temp_change"] = (
    summary["after_avg_coolant_temp"]
    - summary["before_avg_coolant_temp"]
)

summary = summary.sort_values(
    "temp_change",
    ascending=False
)

fleet_before_avg = summary[
    "before_avg_coolant_temp"
].mean()

fleet_after_avg = summary[
    "after_avg_coolant_temp"
].mean()

fleet_change = (
    fleet_after_avg
    - fleet_before_avg
)

fleet_summary = pd.DataFrame([
    {
        "metric": "fleet_before_avg_temp",
        "value": fleet_before_avg
    },
    {
        "metric": "fleet_after_avg_temp",
        "value": fleet_after_avg
    },
    {
        "metric": "fleet_temp_change",
        "value": fleet_change
    }
])

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

summary.to_csv(
    output_path,
    index=False
)

fleet_summary.to_csv(
    fleet_output_path,
    index=False
)

print("\nVehicle summary saved")
print(output_path)

print("\nFleet summary saved")
print(fleet_output_path)

print("\nFleet Temperature Comparison")
print(f"Before Avg: {fleet_before_avg:.2f}")
print(f"After Avg : {fleet_after_avg:.2f}")
print(f"Change    : {fleet_change:.2f}")

print("\nTop Temperature Increases")
print(summary.head())