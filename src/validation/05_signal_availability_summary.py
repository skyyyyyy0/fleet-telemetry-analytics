import pandas as pd
import ast
from pathlib import Path

raw_path = Path("data/raw/geotab_statusdata_raw_full.csv")
output_path = Path("outputs/signal_availability_summary.csv")

df = pd.read_csv(raw_path)

def get_diagnostic_id(value):
    try:
        value = ast.literal_eval(value)
        return value.get("id")
    except:
        return None

df["diagnostic_id"] = df["diagnostic"].apply(get_diagnostic_id)

signal_map = {
    "DiagnosticEngineRoadSpeedId": "vehicle_speed",
    "DiagnosticEngineSpeedId": "engine_rpm",
    "DiagnosticDeviceTotalFuelId": "fuel_used",
    "DiagnosticOdometerId": "odometer",
    "DiagnosticRawOdometerId": "raw_odometer",
    "DiagnosticGenericIncrementalDistanceId)": "incremental_distance",
    "DiagnosticAccelerationForwardBrakingId": "forward_braking",
    "DiagnosticAccelerationSideToSideId": "side_acceleration",
    "DiagnosticAccelerationUpDownId": "up_down_acceleration",
    "DiagnosticEngineCoolantTemperatureId": "coolant_temp"
}

df = df[df["diagnostic_id"].isin(signal_map.keys())].copy()
df["signal"] = df["diagnostic_id"].map(signal_map)

summary = (
    df.groupby(["vehicle", "signal"])
    .size()
    .reset_index(name="record_count")
)

summary_pivot = (
    summary.pivot_table(
        index="vehicle",
        columns="signal",
        values="record_count",
        fill_value=0
    )
    .reset_index()
)

expected_signals = [
    "vehicle_speed",
    "engine_rpm",
    "fuel_used",
    "odometer",
    "raw_odometer",
    "incremental_distance",
    "forward_braking",
    "side_acceleration",
    "up_down_acceleration",
    "coolant_temp"
]

for signal in expected_signals:
    if signal not in summary_pivot.columns:
        summary_pivot[signal] = 0

summary_pivot["has_speed"] = summary_pivot["vehicle_speed"] > 0
summary_pivot["has_rpm"] = summary_pivot["engine_rpm"] > 0
summary_pivot["has_fuel"] = summary_pivot["fuel_used"] > 0
summary_pivot["has_distance"] = (
    (summary_pivot["odometer"] > 0)
    | (summary_pivot["raw_odometer"] > 0)
    | (summary_pivot["incremental_distance"] > 0)
)

summary_pivot["fei_lite_ready"] = (
    summary_pivot["has_speed"]
    & summary_pivot["has_rpm"]
    & summary_pivot["has_fuel"]
    & summary_pivot["has_distance"]
)

output_path.parent.mkdir(parents=True, exist_ok=True)
summary_pivot.to_csv(output_path, index=False)

print("Signal availability summary saved")
print(f"Output: {output_path}")
print("\nVehicle count:")
print(len(summary_pivot))

print("\nFEI-Lite readiness:")
print(summary_pivot["fei_lite_ready"].value_counts())

print("\nSummary preview:")
print(summary_pivot.head())