import pandas as pd
import ast
from pathlib import Path

raw_path = Path("data/raw/geotab_statusdata_raw_full.csv")
output_path = Path("data/processed/clean_dataset.csv")

df = pd.read_csv(raw_path)

print("Raw dataset loaded")
print(f"Rows: {len(df)}")

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
    "DiagnosticEngineCoolantTemperatureId": "coolant_temp"
}

clean_df = df[df["diagnostic_id"].isin(signal_map.keys())].copy()

clean_df["signal"] = clean_df["diagnostic_id"].map(signal_map)
clean_df["dateTime"] = (
    pd.to_datetime(clean_df["dateTime"], errors="coerce", utc=True)
    .dt.tz_convert("Asia/Seoul")
)
clean_df["data"] = pd.to_numeric(clean_df["data"], errors="coerce")

clean_df = clean_df[
    ["vehicle", "dateTime", "signal", "data", "diagnostic_id"]
].copy()

clean_df = clean_df.dropna(subset=["vehicle", "dateTime", "signal", "data"])

clean_df = clean_df[clean_df["data"] >= 0]

clean_df = clean_df.sort_values(
    by=["vehicle", "dateTime", "signal"]
).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)

clean_df.to_csv(output_path, index=False)

print("Clean dataset saved")
print(f"Rows saved: {len(clean_df)}")
print(f"Output: {output_path}")

print("\nSignal counts")
print(clean_df["signal"].value_counts())

print("\nVehicle counts")
print(clean_df["vehicle"].value_counts())