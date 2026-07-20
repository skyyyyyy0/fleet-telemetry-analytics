from pathlib import Path

import numpy as np
import pandas as pd


DATASETS = {
    "before": Path(
        "data/processed/before_clean_dataset.csv"
    ),
    "after": Path(
        "data/processed/after_clean_dataset.csv"
    ),
}

PERIOD_PATH = Path("config/analysis_periods.csv")

OUTPUT_PATH = Path(
    "data/processed/data_quality_summary.csv"
)

FLEET_OUTPUT_PATH = Path(
    "outputs/tables/data_quality_fleet_summary.csv"
)

TIMEZONE = "Asia/Seoul"
MAX_GAP_SECONDS = 300
MAX_FUEL_RATE_LPH = 100
MAX_SPEED_KMH = 160

EXPECTED_SIGNALS = [
    "vehicle_speed",
    "engine_rpm",
    "fuel_used",
    "odometer",
    "raw_odometer",
    "incremental_distance",
    "coolant_temp",
    "forward_braking",
    "side_acceleration",
    "up_down_acceleration",
]

VALUE_RANGES = {
    "vehicle_speed": (0, 160),
    "engine_rpm": (0, 4500),
    "fuel_used": (0, np.inf),
    "odometer": (0, np.inf),
    "raw_odometer": (0, np.inf),
    "incremental_distance": (0, np.inf),
    "coolant_temp": (-40, 130),
    "forward_braking": (-np.inf, np.inf),
    "side_acceleration": (-np.inf, np.inf),
    "up_down_acceleration": (-np.inf, np.inf),
}

CUMULATIVE_RULES = {
    "fuel_used": {
        "unit_divisor": 1,
        "max_rate_per_hour": MAX_FUEL_RATE_LPH,
    },
    "odometer": {
        "unit_divisor": 1000,
        "max_rate_per_hour": MAX_SPEED_KMH,
    },
    "raw_odometer": {
        "unit_divisor": 1000,
        "max_rate_per_hour": MAX_SPEED_KMH,
    },
}

EVENT_THRESHOLDS = {
    "forward_braking": 3.0,
    "side_acceleration": 3.0,
}

EVENT_MERGE_GAP_SECONDS = 5


def to_kst_timestamp(value):
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        return timestamp.tz_localize(TIMEZONE)

    return timestamp.tz_convert(TIMEZONE)


def load_periods():
    periods = pd.read_csv(PERIOD_PATH)

    required_columns = {
        "vehicle_id",
        "before_start",
        "before_end_exclusive",
        "after_start",
        "after_end_exclusive",
    }

    missing_columns = (
        required_columns - set(periods.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing period columns: "
            f"{sorted(missing_columns)}"
        )

    if periods["vehicle_id"].duplicated().any():
        raise ValueError(
            "Duplicate vehicle IDs in analysis periods"
        )

    return periods.set_index("vehicle_id")


def get_expected_period(periods, vehicle, period):
    row = periods.loc[vehicle]

    start = to_kst_timestamp(
        row[f"{period}_start"]
    )

    end = to_kst_timestamp(
        row[f"{period}_end_exclusive"]
    )

    return start, end


def count_distinct_events(signal_df, threshold):
    event_df = signal_df.loc[
        signal_df["data"].ge(threshold),
        ["dateTime", "data"],
    ].dropna()

    event_df = (
        event_df
        .groupby("dateTime", as_index=False)["data"]
        .max()
        .sort_values("dateTime")
        .reset_index(drop=True)
    )

    if event_df.empty:
        return 0

    gaps = event_df["dateTime"].diff().dt.total_seconds()

    return int(
        (
            gaps.isna()
            | gaps.gt(EVENT_MERGE_GAP_SECONDS)
        ).sum()
    )


def analyze_signal(
    signal_df,
    vehicle,
    period,
    signal,
    expected_start,
    expected_end,
):
    work = signal_df[
        ["dateTime", "data"]
    ].copy()

    # Ensure datetime dtype even when the signal DataFrame is empty.
    work["dateTime"] = (
        pd.to_datetime(
            work["dateTime"],
            errors="coerce",
            utc=True,
        )
        .dt.tz_convert(TIMEZONE)
    )

    input_record_count = len(work)

    input_record_count = len(work)

    work["data"] = pd.to_numeric(
        work["data"],
        errors="coerce",
    )

    invalid_timestamp_count = int(
        work["dateTime"].isna().sum()
    )

    invalid_numeric_count = int(
        work["data"].isna().sum()
    )

    timestamp_valid = work.dropna(
        subset=["dateTime"]
    ).copy()

    outside_period_count = int(
        (
            timestamp_valid["dateTime"].lt(expected_start)
            | timestamp_valid["dateTime"].ge(expected_end)
        ).sum()
    )

    duplicate_timestamp_count = int(
        timestamp_valid.duplicated(
            subset=["dateTime"],
            keep="last",
        ).sum()
    )

    work = (
        timestamp_valid
        .sort_values("dateTime")
        .drop_duplicates(
            subset=["dateTime"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    minimum, maximum = VALUE_RANGES[signal]

    work["valid_value"] = (
        work["data"].notna()
        & work["data"].between(
            minimum,
            maximum,
            inclusive="both",
        )
    )

    outlier_value_count = int(
        (~work["valid_value"]).sum()
    )

    work["time_delta_seconds"] = (
        work["dateTime"].shift(-1)
        - work["dateTime"]
    ).dt.total_seconds()

    interval_candidate = (
        work["time_delta_seconds"].notna()
    )

    interval_candidate_count = int(
        interval_candidate.sum()
    )

    nonpositive_interval_count = int(
        (
            interval_candidate
            & work["time_delta_seconds"].le(0)
        ).sum()
    )

    long_gap_count = int(
        (
            interval_candidate
            & work["time_delta_seconds"].gt(
                MAX_GAP_SECONDS
            )
        ).sum()
    )

    valid_interval = (
        interval_candidate
        & work["valid_value"]
        & work["time_delta_seconds"].gt(0)
        & work["time_delta_seconds"].le(
            MAX_GAP_SECONDS
        )
    )

    valid_interval_count = int(
        valid_interval.sum()
    )

    removed_interval_count = (
        interval_candidate_count
        - valid_interval_count
    )

    if interval_candidate_count > 0:
        removed_interval_pct = (
            removed_interval_count
            / interval_candidate_count
            * 100
        )
    else:
        removed_interval_pct = np.nan

    valid_time_hours = (
        work.loc[
            valid_interval,
            "time_delta_seconds",
        ].sum()
        / 3600
    )

    first_timestamp = (
        work["dateTime"].min()
        if not work.empty
        else pd.NaT
    )

    last_timestamp = (
        work["dateTime"].max()
        if not work.empty
        else pd.NaT
    )

    expected_hours = (
        expected_end - expected_start
    ).total_seconds() / 3600

    if pd.notna(first_timestamp):
        start_delay_hours = (
            first_timestamp - expected_start
        ).total_seconds() / 3600
    else:
        start_delay_hours = np.nan

    if pd.notna(last_timestamp):
        end_shortfall_hours = (
            expected_end - last_timestamp
        ).total_seconds() / 3600
    else:
        end_shortfall_hours = np.nan

    if (
        pd.notna(first_timestamp)
        and pd.notna(last_timestamp)
        and expected_hours > 0
    ):
        observed_span_pct = (
            (
                last_timestamp - first_timestamp
            ).total_seconds()
            / 3600
            / expected_hours
            * 100
        )
    else:
        observed_span_pct = 0.0

    reset_count = np.nan
    excessive_rate_count = np.nan
    valid_increment_count = np.nan
    removed_increment_count = np.nan
    removed_increment_pct = np.nan

    if signal in CUMULATIVE_RULES:
        rule = CUMULATIVE_RULES[signal]

        work["previous_valid_value"] = (
            work["valid_value"].shift(
                1,
                fill_value=False,
            )
        )

        work["previous_delta_seconds"] = (
            work["dateTime"].diff()
        ).dt.total_seconds()

        work["change"] = (
            work["data"].diff()
            / rule["unit_divisor"]
        )

        work["rate_per_hour"] = (
            work["change"]
            * 3600
            / work["previous_delta_seconds"]
        )

        comparable = (
            work["valid_value"]
            & work["previous_valid_value"]
            & work["previous_delta_seconds"].gt(0)
        )

        reset_mask = (
            comparable
            & work["change"].lt(0)
        )

        excessive_rate_mask = (
            comparable
            & work["change"].ge(0)
            & work["rate_per_hour"].gt(
                rule["max_rate_per_hour"]
            )
        )

        valid_increment_mask = (
            comparable
            & work["change"].ge(0)
            & work["rate_per_hour"].le(
                rule["max_rate_per_hour"]
            )
        )

        comparable_count = int(comparable.sum())

        reset_count = int(reset_mask.sum())
        excessive_rate_count = int(
            excessive_rate_mask.sum()
        )
        valid_increment_count = int(
            valid_increment_mask.sum()
        )

        removed_increment_count = (
            comparable_count
            - valid_increment_count
        )

        if comparable_count > 0:
            removed_increment_pct = (
                removed_increment_count
                / comparable_count
                * 100
            )

    threshold_record_count = np.nan
    distinct_event_count = np.nan

    if signal in EVENT_THRESHOLDS:
        threshold = EVENT_THRESHOLDS[signal]

        threshold_record_count = int(
            (
                work["valid_value"]
                & work["data"].ge(threshold)
            ).sum()
        )

        distinct_event_count = count_distinct_events(
            work[work["valid_value"]],
            threshold,
        )

    return {
        "vehicle": vehicle,
        "period": period,
        "signal": signal,
        "signal_present": input_record_count > 0,
        "expected_start": expected_start,
        "expected_end_exclusive": expected_end,
        "input_record_count": input_record_count,
        "invalid_timestamp_count":
            invalid_timestamp_count,
        "invalid_numeric_count": invalid_numeric_count,
        "duplicate_timestamp_count":
            duplicate_timestamp_count,
        "outlier_value_count": outlier_value_count,
        "outside_period_count": outside_period_count,
        "interval_candidate_count":
            interval_candidate_count,
        "valid_interval_count": valid_interval_count,
        "nonpositive_interval_count":
            nonpositive_interval_count,
        "long_gap_count": long_gap_count,
        "removed_interval_count":
            removed_interval_count,
        "removed_interval_pct":
            removed_interval_pct,
        "valid_time_hours": valid_time_hours,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "expected_period_hours": expected_hours,
        "start_delay_hours": start_delay_hours,
        "end_shortfall_hours":
            end_shortfall_hours,
        "observed_span_pct": observed_span_pct,
        "reset_count": reset_count,
        "excessive_rate_count":
            excessive_rate_count,
        "valid_increment_count":
            valid_increment_count,
        "removed_increment_count":
            removed_increment_count,
        "removed_increment_pct":
            removed_increment_pct,
        "threshold_record_count":
            threshold_record_count,
        "distinct_event_count":
            distinct_event_count,
    }


def main():
    periods = load_periods()
    results = []

    for period, path in DATASETS.items():
        df = pd.read_csv(path)

        required_columns = {
            "vehicle",
            "dateTime",
            "signal",
            "data",
        }

        missing_columns = (
            required_columns - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                f"{path} is missing columns: "
                f"{sorted(missing_columns)}"
            )

        df["dateTime"] = (
            pd.to_datetime(
                df["dateTime"],
                errors="coerce",
                utc=True,
            )
            .dt.tz_convert(TIMEZONE)
        )

        grouped = {
            key: group
            for key, group in df.groupby(
                ["vehicle", "signal"],
                sort=False,
            )
        }

        for vehicle in periods.index:
            expected_start, expected_end = (
                get_expected_period(
                    periods,
                    vehicle,
                    period,
                )
            )

            for signal in EXPECTED_SIGNALS:
                signal_df = grouped.get(
                    (vehicle, signal),
                    pd.DataFrame(
                        columns=[
                            "dateTime",
                            "data",
                        ]
                    ),
                )

                results.append(
                    analyze_signal(
                        signal_df=signal_df,
                        vehicle=vehicle,
                        period=period,
                        signal=signal,
                        expected_start=expected_start,
                        expected_end=expected_end,
                    )
                )

    quality_df = pd.DataFrame(results)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    FLEET_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    quality_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    fleet_summary = (
        quality_df
        .groupby(
            ["period", "signal"],
            as_index=False,
        )
        .agg(
            vehicle_count=("vehicle", "nunique"),
            vehicles_with_signal=(
                "signal_present",
                "sum",
            ),
            input_record_count=(
                "input_record_count",
                "sum",
            ),
            outlier_value_count=(
                "outlier_value_count",
                "sum",
            ),
            duplicate_timestamp_count=(
                "duplicate_timestamp_count",
                "sum",
            ),
            interval_candidate_count=(
                "interval_candidate_count",
                "sum",
            ),
            valid_interval_count=(
                "valid_interval_count",
                "sum",
            ),
            long_gap_count=(
                "long_gap_count",
                "sum",
            ),
            removed_interval_count=(
                "removed_interval_count",
                "sum",
            ),
            reset_count=("reset_count", "sum"),
            excessive_rate_count=(
                "excessive_rate_count",
                "sum",
            ),
            valid_increment_count=(
                "valid_increment_count",
                "sum",
            ),
            removed_increment_count=(
                "removed_increment_count",
                "sum",
            ),
        )
    )

    fleet_summary["removed_interval_pct"] = (
        fleet_summary["removed_interval_count"]
        / fleet_summary[
            "interval_candidate_count"
        ].replace(0, np.nan)
        * 100
    )

    fleet_summary["removed_increment_pct"] = (
        fleet_summary["removed_increment_count"]
        / (
            fleet_summary["valid_increment_count"]
            + fleet_summary[
                "removed_increment_count"
            ]
        ).replace(0, np.nan)
        * 100
    )

    fleet_summary.to_csv(
        FLEET_OUTPUT_PATH,
        index=False,
    )

    print("Data quality summary saved")
    print(f"Detail: {OUTPUT_PATH}")
    print(f"Fleet: {FLEET_OUTPUT_PATH}")
    print(f"Detail rows: {len(quality_df)}")

    print("\nSignal availability")
    print(
        fleet_summary[
            [
                "period",
                "signal",
                "vehicles_with_signal",
                "vehicle_count",
                "removed_interval_pct",
                "reset_count",
                "excessive_rate_count",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()