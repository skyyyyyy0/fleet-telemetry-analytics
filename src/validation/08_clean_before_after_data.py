import pandas as pd
import ast
from pathlib import Path

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

files = {
    "before": {
        "input": "data/raw/before_statusdata_raw.csv",
        "clean_output": "data/processed/before_clean_dataset.csv",
        "summary_output": "outputs/tables/before_signal_summary.csv"
    },
    "after": {
        "input": "data/raw/after_statusdata_raw.csv",
        "clean_output": "data/processed/after_clean_dataset.csv",
        "summary_output": "outputs/tables/after_signal_summary.csv"
    }
}

def get_diagnostic_id(value):
    try:
        value = ast.literal_eval(value)
        return value.get("id")
    except:
        return None

def clean_dataset(period_name, input_path, clean_output, summary_output):
    print(f"\nCleaning {period_name.upper()} dataset")

    df = pd.read_csv(input_path)

    print(f"Raw rows: {len(df)}")

    df["diagnostic_id"] = df["diagnostic"].apply(get_diagnostic_id)

    clean_df = df[df["diagnostic_id"].isin(signal_map.keys())].copy()

    clean_df["signal"] = clean_df["diagnostic_id"].map(signal_map)
    clean_df["dateTime"] = pd.to_datetime(clean_df["dateTime"], errors="coerce")
    clean_df["data"] = pd.to_numeric(clean_df["data"], errors="coerce")

    clean_df = clean_df[
        ["vehicle", "period", "dateTime", "signal", "data", "diagnostic_id"]
    ].copy()

    clean_df = clean_df.dropna(subset=["vehicle", "period", "dateTime", "signal", "data"])

    clean_df = clean_df[clean_df["data"] >= 0]

    clean_df = clean_df.sort_values(
        by=["vehicle", "dateTime", "signal"]
    ).reset_index(drop=True)

    Path(clean_output).parent.mkdir(parents=True, exist_ok=True)
    Path(summary_output).parent.mkdir(parents=True, exist_ok=True)

    clean_df.to_csv(clean_output, index=False)

    summary = (
        clean_df.groupby(["vehicle", "signal"])
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

    summary_pivot["has_speed"] = summary_pivot.get("vehicle_speed", 0) > 0
    summary_pivot["has_rpm"] = summary_pivot.get("engine_rpm", 0) > 0
    summary_pivot["has_fuel"] = summary_pivot.get("fuel_used", 0) > 0

    summary_pivot["has_distance"] = (
        (summary_pivot.get("odometer", 0) > 0)
        | (summary_pivot.get("raw_odometer", 0) > 0)
        | (summary_pivot.get("incremental_distance", 0) > 0)
    )

    summary_pivot["kpi_ready"] = (
        summary_pivot["has_speed"]
        & summary_pivot["has_rpm"]
        & summary_pivot["has_fuel"]
        & summary_pivot["has_distance"]
    )

    summary_pivot.to_csv(summary_output, index=False)

    print(f"Clean rows: {len(clean_df)}")
    print(f"Clean output: {clean_output}")
    print(f"Summary output: {summary_output}")

    print("\nSignal counts")
    print(clean_df["signal"].value_counts())

    print("\nKPI readiness")
    print(summary_pivot["kpi_ready"].value_counts())

for period_name, paths in files.items():
    clean_dataset(
        period_name,
        paths["input"],
        paths["clean_output"],
        paths["summary_output"]
    )