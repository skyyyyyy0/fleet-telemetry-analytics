import pandas as pd
from pathlib import Path

before_path = Path("data/processed/before_clean_dataset.csv")
after_path = Path("data/processed/after_clean_dataset.csv")
output_path = Path("data/processed/vehicle_kpi_dataset.csv")


def calculate_distance(vehicle_df):
    odometer_df = vehicle_df[vehicle_df["signal"] == "odometer"].copy()
    raw_odometer_df = vehicle_df[vehicle_df["signal"] == "raw_odometer"].copy()
    incremental_df = vehicle_df[vehicle_df["signal"] == "incremental_distance"].copy()

    if len(odometer_df) > 1:
        return (odometer_df["data"].max() - odometer_df["data"].min()) / 1000

    if len(raw_odometer_df) > 1:
        return (raw_odometer_df["data"].max() - raw_odometer_df["data"].min()) / 1000

    if len(incremental_df) > 0:
        return incremental_df["data"].sum() / 1000

    return 0


def calculate_fuel(vehicle_df):
    fuel_df = vehicle_df[vehicle_df["signal"] == "fuel_used"].copy()

    if len(fuel_df) > 1:
        return fuel_df["data"].max() - fuel_df["data"].min()

    return 0


def calculate_rpm_metrics(vehicle_df):
    rpm_df = vehicle_df[vehicle_df["signal"] == "engine_rpm"].copy()

    if rpm_df.empty:
        return 0, 0

    avg_rpm = rpm_df["data"].mean()

    efficient_rpm = rpm_df[
        (rpm_df["data"] >= 1200) &
        (rpm_df["data"] <= 1800)
    ]

    rpm_efficiency_ratio = len(efficient_rpm) / len(rpm_df)

    return avg_rpm, rpm_efficiency_ratio


def calculate_speed_metrics(vehicle_df):
    speed_df = vehicle_df[vehicle_df["signal"] == "vehicle_speed"].copy()

    if speed_df.empty:
        return 0

    return speed_df["data"].mean()


def calculate_idle_ratio(vehicle_df):
    speed_df = vehicle_df[vehicle_df["signal"] == "vehicle_speed"][["dateTime", "data"]].copy()
    rpm_df = vehicle_df[vehicle_df["signal"] == "engine_rpm"][["dateTime", "data"]].copy()

    if speed_df.empty or rpm_df.empty:
        return 0

    speed_df = speed_df.rename(columns={"data": "speed"})
    rpm_df = rpm_df.rename(columns={"data": "rpm"})

    speed_df = speed_df.sort_values("dateTime")
    rpm_df = rpm_df.sort_values("dateTime")

    merged = pd.merge_asof(
        speed_df,
        rpm_df,
        on="dateTime",
        direction="nearest",
        tolerance=pd.Timedelta("60s")
    )

    merged = merged.dropna(subset=["speed", "rpm"])

    if merged.empty:
        return 0

    idle_rows = merged[
        (merged["speed"] < 1) &
        (merged["rpm"] > 500)
    ]

    idle_ratio = len(idle_rows) / len(merged)

    return idle_ratio


def calculate_driving_events(vehicle_df):
    harsh_braking_count = len(vehicle_df[vehicle_df["signal"] == "forward_braking"])
    side_accel_count = len(vehicle_df[vehicle_df["signal"] == "side_acceleration"])

    return harsh_braking_count, side_accel_count


def build_kpi_dataset(input_path, period_name):
    df = pd.read_csv(input_path)
    df["dateTime"] = pd.to_datetime(df["dateTime"], errors="coerce")

    results = []

    for vehicle, vehicle_df in df.groupby("vehicle"):
        vehicle_df = vehicle_df.sort_values("dateTime").copy()

        distance_km = calculate_distance(vehicle_df)
        fuel_used_l = calculate_fuel(vehicle_df)

        if fuel_used_l > 0:
            fuel_efficiency = distance_km / fuel_used_l
        else:
            fuel_efficiency = 0

        avg_rpm, rpm_efficiency_ratio = calculate_rpm_metrics(vehicle_df)
        avg_speed = calculate_speed_metrics(vehicle_df)
        idle_ratio = calculate_idle_ratio(vehicle_df)
        harsh_braking_count, side_accel_count = calculate_driving_events(vehicle_df)

        results.append({
            "vehicle": vehicle,
            "period": period_name,
            "analysis_start": vehicle_df["dateTime"].min(),
            "analysis_end": vehicle_df["dateTime"].max(),
            "distance_km": distance_km,
            "fuel_used_l": fuel_used_l,
            "fuel_efficiency_km_l": fuel_efficiency,
            "avg_speed_kmh": avg_speed,
            "avg_rpm": avg_rpm,
            "rpm_efficiency_ratio": rpm_efficiency_ratio,
            "idle_ratio": idle_ratio,
            "harsh_braking_count": harsh_braking_count,
            "side_accel_count": side_accel_count,
            "record_count": len(vehicle_df)
        })

    return pd.DataFrame(results)


before_kpi = build_kpi_dataset(before_path, "before")
after_kpi = build_kpi_dataset(after_path, "after")

kpi_df = pd.concat([before_kpi, after_kpi], ignore_index=True)

kpi_df = kpi_df.sort_values(["vehicle", "period"]).reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
kpi_df.to_csv(output_path, index=False)

print("Vehicle KPI dataset saved")
print(f"Output: {output_path}")
print(f"Rows: {len(kpi_df)}")

print("\nPeriod counts")
print(kpi_df["period"].value_counts())

print("\nPreview")
print(kpi_df.head())