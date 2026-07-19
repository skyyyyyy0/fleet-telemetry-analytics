import pandas as pd
from pathlib import Path

input_path = Path("data/processed/vehicle_kpi_dataset.csv")
output_path = Path("data/processed/fes_scores.csv")
summary_path = Path("outputs/tables/fes_summary.csv")

df = pd.read_csv(input_path)

print("KPI dataset loaded")
print(f"Rows: {len(df)}")


def get_vehicle_class(vehicle_name):
    vehicle_name = str(vehicle_name)

    heavy_duty_vehicles = [
        "HDV_01",
        "HDV_02",
        "HDV_03",
        "HDV_04"
    ]

    for vehicle_id in heavy_duty_vehicles:
        if vehicle_id in vehicle_name:
            return "11.5Ton Xcient"

    return "1Ton Porter"


df["vehicle_class"] = df["vehicle"].apply(get_vehicle_class)

before_df = df[df["period"] == "before"].copy()
after_df = df[df["period"] == "after"].copy()

print(f"Before rows: {len(before_df)}")
print(f"After rows: {len(after_df)}")

before_baseline = (
    before_df
    .groupby("vehicle_class")["fuel_efficiency_km_l"]
    .median()
    .reset_index()
    .rename(columns={
        "fuel_efficiency_km_l": "class_before_median_fe"
    })
)

before_df = before_df[[
    "vehicle",
    "vehicle_class",
    "fuel_efficiency_km_l"
]].rename(columns={
    "fuel_efficiency_km_l": "before_fuel_efficiency_km_l"
})

after_df = after_df[[
    "vehicle",
    "vehicle_class",
    "fuel_efficiency_km_l"
]].rename(columns={
    "fuel_efficiency_km_l": "after_fuel_efficiency_km_l"
})

fes_df = before_df.merge(
    after_df,
    on=["vehicle", "vehicle_class"],
    how="inner"
)

fes_df = fes_df.merge(
    before_baseline,
    on="vehicle_class",
    how="left"
)

fes_df["before_fes_raw"] = (
    fes_df["before_fuel_efficiency_km_l"]
    / fes_df["class_before_median_fe"]
) * 100

fes_df["after_fes_raw"] = (
    fes_df["after_fuel_efficiency_km_l"]
    / fes_df["class_before_median_fe"]
) * 100

fes_df["before_fes"] = fes_df["before_fes_raw"].clip(upper=100)
fes_df["after_fes"] = fes_df["after_fes_raw"].clip(upper=100)

fes_df["fuel_efficiency_change_pct"] = (
    (
        fes_df["after_fuel_efficiency_km_l"]
        - fes_df["before_fuel_efficiency_km_l"]
    )
    / fes_df["before_fuel_efficiency_km_l"]
) * 100

fes_df["fes_change"] = (
    fes_df["after_fes"]
    - fes_df["before_fes"]
)

fes_df = fes_df.sort_values(
    "fuel_efficiency_change_pct",
    ascending=False
).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.parent.mkdir(parents=True, exist_ok=True)

fes_df.to_csv(output_path, index=False)

class_summary = (
    fes_df
    .groupby("vehicle_class")
    .agg(
        vehicle_count=("vehicle", "count"),
        class_before_median_fe=("class_before_median_fe", "first"),
        avg_before_fe=("before_fuel_efficiency_km_l", "mean"),
        avg_after_fe=("after_fuel_efficiency_km_l", "mean"),
        avg_before_fes=("before_fes", "mean"),
        avg_after_fes=("after_fes", "mean"),
        avg_fes_change=("fes_change", "mean"),
        avg_fe_change_pct=("fuel_efficiency_change_pct", "mean")
    )
    .reset_index()
)

summary = pd.DataFrame([
    {
        "metric": "fleet_avg_before_fes",
        "value": fes_df["before_fes"].mean()
    },
    {
        "metric": "fleet_avg_after_fes",
        "value": fes_df["after_fes"].mean()
    },
    {
        "metric": "fleet_avg_fes_change",
        "value": fes_df["fes_change"].mean()
    },
    {
        "metric": "fleet_avg_fuel_efficiency_change_pct",
        "value": fes_df["fuel_efficiency_change_pct"].mean()
    },
    {
        "metric": "vehicles_improved",
        "value": (fes_df["fuel_efficiency_change_pct"] > 0).sum()
    },
    {
        "metric": "vehicles_declined",
        "value": (fes_df["fuel_efficiency_change_pct"] < 0).sum()
    },
    {
        "metric": "heavy_duty_vehicle_count",
        "value": (fes_df["vehicle_class"] == "11.5Ton Xcient").sum()
    },
    {
        "metric": "porter_vehicle_count",
        "value": (fes_df["vehicle_class"] == "1Ton Porter").sum()
    }
])

summary.to_csv(summary_path, index=False)

class_summary_path = Path("outputs/tables/fes_class_summary.csv")
class_summary.to_csv(class_summary_path, index=False)

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
print(fes_df[[
    "vehicle",
    "vehicle_class",
    "before_fuel_efficiency_km_l",
    "after_fuel_efficiency_km_l",
    "fuel_efficiency_change_pct",
    "before_fes",
    "after_fes",
    "fes_change"
]].head())