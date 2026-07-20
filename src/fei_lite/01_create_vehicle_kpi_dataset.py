import pandas as pd
from pathlib import Path

before_path = Path("data/processed/before_clean_dataset.csv")
after_path = Path("data/processed/after_clean_dataset.csv")
output_path = Path("data/processed/vehicle_kpi_dataset.csv")

MAX_GAP_SECONDS = 300
MAX_SPEED_KMH = 160
MAX_RPM = 4500
ENGINE_ON_RPM = 500
EFFICIENT_RPM_MIN = 1200
EFFICIENT_RPM_MAX = 1800
MAX_FUEL_RATE_LPH = 100
METERS_PER_KM = 1000
HARSH_BRAKING_THRESHOLD = 3.0
SIDE_ACCEL_THRESHOLD = 3.0
EVENT_MERGE_GAP_SECONDS = 5

def prepare_signal_intervals(
    vehicle_df,
    signal_name,
    min_value,
    max_value,
):
    signal_df = vehicle_df.loc[
        vehicle_df["signal"] == signal_name,
        ["dateTime", "data"],
    ].copy()

    signal_df["data"] = pd.to_numeric(
        signal_df["data"],
        errors="coerce",
    )

    signal_df = (
        signal_df
        .dropna(subset=["dateTime"])
        .sort_values("dateTime")
        .drop_duplicates(subset=["dateTime"], keep="last")
        .reset_index(drop=True)
    )

    signal_df["time_delta_seconds"] = (
        signal_df["dateTime"].shift(-1)
        - signal_df["dateTime"]
    ).dt.total_seconds()

    signal_df["valid_value"] = signal_df["data"].between(
        min_value,
        max_value,
        inclusive="both",
    )

    signal_df["valid_interval"] = (
        signal_df["valid_value"]
        & signal_df["time_delta_seconds"].gt(0)
        & signal_df["time_delta_seconds"].le(MAX_GAP_SECONDS)
    )

    return signal_df

def calculate_cumulative_increase(
    vehicle_df,
    signal_name,
    unit_divisor,
    max_rate_per_hour,
):
    counter_df = vehicle_df.loc[
        vehicle_df["signal"] == signal_name,
        ["dateTime", "data"],
    ].copy()

    raw_record_count = len(counter_df)

    counter_df["data"] = pd.to_numeric(
        counter_df["data"],
        errors="coerce",
    )

    invalid_timestamp_count = counter_df[
        "dateTime"
    ].isna().sum()

    counter_df = (
        counter_df
        .dropna(subset=["dateTime"])
        .sort_values("dateTime")
    )

    duplicate_timestamp_count = counter_df.duplicated(
        subset=["dateTime"],
        keep="last",
    ).sum()

    counter_df = (
        counter_df
        .drop_duplicates(
            subset=["dateTime"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    counter_df["valid_value"] = (
        counter_df["data"].notna()
        & counter_df["data"].ge(0)
    )

    counter_df["previous_valid_value"] = (
        counter_df["valid_value"].shift(
            1,
            fill_value=False,
        )
    )

    counter_df["change"] = (
        counter_df["data"].diff() / unit_divisor
    )

    counter_df["time_delta_seconds"] = (
        counter_df["dateTime"].diff()
    ).dt.total_seconds()

    counter_df["rate_per_hour"] = (
        counter_df["change"]
        * 3600
        / counter_df["time_delta_seconds"]
    )

    comparable = (
        counter_df["valid_value"]
        & counter_df["previous_valid_value"]
        & counter_df["time_delta_seconds"].gt(0)
    )

    reset_mask = (
        comparable
        & counter_df["change"].lt(0)
    )

    excessive_rate_mask = (
        comparable
        & counter_df["change"].ge(0)
        & counter_df["rate_per_hour"].gt(
            max_rate_per_hour
        )
    )

    valid_increment_mask = (
        comparable
        & counter_df["change"].ge(0)
        & counter_df["rate_per_hour"].le(
            max_rate_per_hour
        )
    )

    if valid_increment_mask.any():
        total_increase = counter_df.loc[
            valid_increment_mask,
            "change",
        ].sum()
    else:
        total_increase = float("nan")

    quality = {
        "signal": signal_name,
        "raw_record_count": raw_record_count,
        "invalid_timestamp_count": int(
            invalid_timestamp_count
        ),
        "duplicate_timestamp_count": int(
            duplicate_timestamp_count
        ),
        "reset_count": int(reset_mask.sum()),
        "excessive_rate_count": int(
            excessive_rate_mask.sum()
        ),
        "valid_increment_count": int(
            valid_increment_mask.sum()
        ),
    }

    return total_increase, quality

def calculate_distance(vehicle_df):
    odometer_distance, _ = calculate_cumulative_increase(
        vehicle_df=vehicle_df,
        signal_name="odometer",
        unit_divisor=METERS_PER_KM,
        max_rate_per_hour=MAX_SPEED_KMH,
    )

    if pd.notna(odometer_distance):
        return odometer_distance

    raw_odometer_distance, _ = calculate_cumulative_increase(
        vehicle_df=vehicle_df,
        signal_name="raw_odometer",
        unit_divisor=METERS_PER_KM,
        max_rate_per_hour=MAX_SPEED_KMH,
    )

    if pd.notna(raw_odometer_distance):
        return raw_odometer_distance

    incremental_df = vehicle_df.loc[
        vehicle_df["signal"] == "incremental_distance",
        ["dateTime", "data"],
    ].copy()

    incremental_df["data"] = pd.to_numeric(
        incremental_df["data"],
        errors="coerce",
    )

    incremental_df = (
        incremental_df
        .dropna(subset=["dateTime", "data"])
        .sort_values("dateTime")
        .drop_duplicates(subset=["dateTime"], keep="last")
        .reset_index(drop=True)
    )

    incremental_df["time_delta_seconds"] = (
        incremental_df["dateTime"].diff()
    ).dt.total_seconds()

    incremental_df["distance_km"] = (
        incremental_df["data"] / METERS_PER_KM
    )

    incremental_df["implied_speed_kmh"] = (
        incremental_df["distance_km"]
        * 3600
        / incremental_df["time_delta_seconds"]
    )

    valid_increment_df = incremental_df[
        incremental_df["data"].ge(0)
        & incremental_df["time_delta_seconds"].gt(0)
        & incremental_df["implied_speed_kmh"].le(
            MAX_SPEED_KMH
        )
    ]

    if valid_increment_df.empty:
        return float("nan")

    return valid_increment_df["distance_km"].sum()


def calculate_fuel(vehicle_df):
    fuel_used_l, _ = calculate_cumulative_increase(
        vehicle_df=vehicle_df,
        signal_name="fuel_used",
        unit_divisor=1,
        max_rate_per_hour=MAX_FUEL_RATE_LPH,
    )

    return fuel_used_l


def calculate_rpm_metrics(vehicle_df):
    rpm_df = prepare_signal_intervals(
        vehicle_df=vehicle_df,
        signal_name="engine_rpm",
        min_value=0,
        max_value=MAX_RPM,
    )

    engine_on_df = rpm_df[
        rpm_df["valid_interval"]
        & rpm_df["data"].gt(ENGINE_ON_RPM)
    ].copy()

    engine_on_seconds = engine_on_df[
        "time_delta_seconds"
    ].sum()

    if engine_on_seconds <= 0:
        return float("nan"), float("nan")

    avg_rpm = (
        engine_on_df["data"]
        * engine_on_df["time_delta_seconds"]
    ).sum() / engine_on_seconds

    efficient_seconds = engine_on_df.loc[
        engine_on_df["data"].between(
            EFFICIENT_RPM_MIN,
            EFFICIENT_RPM_MAX,
            inclusive="both",
        ),
        "time_delta_seconds",
    ].sum()

    rpm_efficiency_ratio = (
        efficient_seconds / engine_on_seconds
    )

    return avg_rpm, rpm_efficiency_ratio


def calculate_speed_metrics(vehicle_df):
    speed_df = prepare_signal_intervals(
        vehicle_df=vehicle_df,
        signal_name="vehicle_speed",
        min_value=0,
        max_value=MAX_SPEED_KMH,
    )

    valid_speed_df = speed_df[
        speed_df["valid_interval"]
    ].copy()

    total_seconds = valid_speed_df[
        "time_delta_seconds"
    ].sum()

    if total_seconds <= 0:
        return float("nan")

    avg_speed = (
        valid_speed_df["data"]
        * valid_speed_df["time_delta_seconds"]
    ).sum() / total_seconds

    return avg_speed


def calculate_idle_metrics(vehicle_df):
    speed_df = prepare_signal_intervals(
        vehicle_df,
        "vehicle_speed",
        0,
        MAX_SPEED_KMH,
    )

    rpm_df = prepare_signal_intervals(
        vehicle_df,
        "engine_rpm",
        0,
        MAX_RPM,
    )

    if speed_df.empty or rpm_df.empty:
        return float("nan"), float("nan"), float("nan")

    speed_df["speed"] = speed_df["data"].where(
        speed_df["valid_value"]
    )
    speed_df["speed_observed_at"] = speed_df["dateTime"]

    rpm_df["rpm"] = rpm_df["data"].where(
        rpm_df["valid_value"]
    )
    rpm_df["rpm_observed_at"] = rpm_df["dateTime"]

    timestamps = (
        pd.concat(
            [speed_df["dateTime"], rpm_df["dateTime"]],
            ignore_index=True,
        )
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    timeline = timestamps.to_frame(name="dateTime")
    tolerance = pd.Timedelta(seconds=MAX_GAP_SECONDS)

    aligned = pd.merge_asof(
        timeline,
        speed_df[
            ["dateTime", "speed", "speed_observed_at"]
        ],
        on="dateTime",
        direction="backward",
        tolerance=tolerance,
    )

    aligned = pd.merge_asof(
        aligned,
        rpm_df[
            ["dateTime", "rpm", "rpm_observed_at"]
        ],
        on="dateTime",
        direction="backward",
        tolerance=tolerance,
    )

    aligned["next_timestamp"] = aligned[
        "dateTime"
    ].shift(-1)

    aligned["raw_time_delta_seconds"] = (
        aligned["next_timestamp"]
        - aligned["dateTime"]
    ).dt.total_seconds()

    aligned["speed_valid_until"] = (
        aligned["speed_observed_at"] + tolerance
    )
    aligned["rpm_valid_until"] = (
        aligned["rpm_observed_at"] + tolerance
    )

    aligned["interval_end"] = aligned["next_timestamp"]

    aligned.loc[
        aligned["speed_valid_until"]
        < aligned["interval_end"],
        "interval_end",
    ] = aligned["speed_valid_until"]

    aligned.loc[
        aligned["rpm_valid_until"]
        < aligned["interval_end"],
        "interval_end",
    ] = aligned["rpm_valid_until"]

    aligned["time_delta_seconds"] = (
        aligned["interval_end"]
        - aligned["dateTime"]
    ).dt.total_seconds()

    valid_df = aligned[
        aligned["speed"].notna()
        & aligned["rpm"].notna()
        & aligned["raw_time_delta_seconds"].gt(0)
        & aligned["raw_time_delta_seconds"].le(
            MAX_GAP_SECONDS
        )
        & aligned["time_delta_seconds"].gt(0)
    ].copy()

    engine_on_df = valid_df[
        valid_df["rpm"].gt(ENGINE_ON_RPM)
    ]

    engine_on_seconds = engine_on_df[
        "time_delta_seconds"
    ].sum()

    if engine_on_seconds <= 0:
        return float("nan"), float("nan"), float("nan")

    idle_seconds = engine_on_df.loc[
        engine_on_df["speed"].lt(1),
        "time_delta_seconds",
    ].sum()

    idle_ratio = idle_seconds / engine_on_seconds

    return idle_ratio, idle_seconds, engine_on_seconds


def summarize_driving_signal(
    vehicle_df,
    signal_name,
    threshold,
):
    signal_df = vehicle_df.loc[
        vehicle_df["signal"] == signal_name,
        ["dateTime", "data"],
    ].copy()

    raw_record_count = len(signal_df)

    if raw_record_count == 0:
        return {
            "record_count": 0,
            "threshold_record_count": float("nan"),
            "event_count": float("nan"),
        }

    signal_df["data"] = pd.to_numeric(
        signal_df["data"],
        errors="coerce",
    )

    signal_df = (
        signal_df
        .dropna(subset=["dateTime", "data"])
        .sort_values("dateTime")
    )

    threshold_record_count = int(
        signal_df["data"].ge(threshold).sum()
    )

    event_df = (
        signal_df[
            signal_df["data"].ge(threshold)
        ]
        .groupby("dateTime", as_index=False)["data"]
        .max()
        .sort_values("dateTime")
        .reset_index(drop=True)
    )

    if event_df.empty:
        event_count = 0
    else:
        event_df["gap_seconds"] = (
            event_df["dateTime"].diff()
        ).dt.total_seconds()

        event_count = int(
            (
                event_df["gap_seconds"].isna()
                | event_df["gap_seconds"].gt(
                    EVENT_MERGE_GAP_SECONDS
                )
            ).sum()
        )

    return {
        "record_count": raw_record_count,
        "threshold_record_count": threshold_record_count,
        "event_count": event_count,
    }


def calculate_driving_events(vehicle_df):
    harsh = summarize_driving_signal(
        vehicle_df,
        "forward_braking",
        HARSH_BRAKING_THRESHOLD,
    )

    side = summarize_driving_signal(
        vehicle_df,
        "side_acceleration",
        SIDE_ACCEL_THRESHOLD,
    )

    return {
        "harsh_braking_record_count": harsh["record_count"],
        "harsh_braking_threshold_record_count": harsh[
            "threshold_record_count"
        ],
        "harsh_braking_event_count": harsh["event_count"],
        "side_accel_record_count": side["record_count"],
        "side_accel_threshold_record_count": side[
            "threshold_record_count"
        ],
        "side_accel_event_count": side["event_count"],
    }


def build_kpi_dataset(input_path, period_name):
    df = pd.read_csv(input_path)
    df["dateTime"] = (
        pd.to_datetime(df["dateTime"], errors="coerce", utc=True)
        .dt.tz_convert("Asia/Seoul")
    )

    results = []

    for vehicle, vehicle_df in df.groupby("vehicle"):
        vehicle_df = vehicle_df.sort_values("dateTime").copy()

        distance_km = calculate_distance(vehicle_df)
        fuel_used_l = calculate_fuel(vehicle_df)

        if (
            pd.notna(distance_km)
            and pd.notna(fuel_used_l)
            and fuel_used_l > 0
        ):
            fuel_efficiency = distance_km / fuel_used_l
        else:
            fuel_efficiency = float("nan")

        avg_rpm, rpm_efficiency_ratio = calculate_rpm_metrics(vehicle_df)
        avg_speed = calculate_speed_metrics(vehicle_df)
        (
            idle_ratio,
            idle_time_seconds,
            engine_on_time_seconds,
        ) = calculate_idle_metrics(vehicle_df)
        driving_event_metrics = calculate_driving_events(
            vehicle_df
        )

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
            "idle_time_hours": idle_time_seconds / 3600,
            "engine_on_time_hours": engine_on_time_seconds / 3600,
            **driving_event_metrics,
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