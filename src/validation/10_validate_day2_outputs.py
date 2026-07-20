from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


KST = ZoneInfo("Asia/Seoul")
ALIAS_PATTERN = r"(?:HDV|LDV)_\d{2}"

FILES = {
    "periods": Path("config/analysis_periods.csv"),
    "kpi": Path(
        "data/processed/vehicle_kpi_dataset.csv"
    ),
    "fes": Path("data/processed/fes_scores.csv"),
    "res": Path("data/processed/res_scores.csv"),
    "ies": Path("data/processed/ies_scores.csv"),
    "dss": Path("data/processed/dss_scores.csv"),
    "quality": Path(
        "data/processed/data_quality_summary.csv"
    ),
    "comparison": Path(
        "outputs/tables/kpi_legacy_vs_v2.csv"
    ),
    "comparison_summary": Path(
        "outputs/tables/kpi_legacy_vs_v2_summary.csv"
    ),
}

errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def to_kst(value):
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        return timestamp.tz_localize(KST)

    return timestamp.tz_convert(KST)


def check_no_infinity(name, frame):
    numeric = frame.select_dtypes(
        include=[np.number]
    )

    if not numeric.empty:
        check(
            not np.isinf(
                numeric.to_numpy()
            ).any(),
            f"{name}: infinite numeric value found",
        )


for name, path in FILES.items():
    check(
        path.exists(),
        f"Missing output file: {path}",
    )

if errors:
    for error in errors:
        print(f"FAIL: {error}")

    raise SystemExit(1)


periods = pd.read_csv(FILES["periods"])

check(
    len(periods) == 12,
    "analysis_periods.csv must contain 12 vehicles",
)

check(
    periods["vehicle_id"].nunique() == 12,
    "analysis_periods.csv contains duplicate vehicles",
)

check(
    periods["vehicle_id"].str.fullmatch(
        ALIAS_PATTERN,
        na=False,
    ).all(),
    "Invalid vehicle alias in analysis_periods.csv",
)

periods = periods.set_index("vehicle_id")
expected_vehicles = set(periods.index)


kpi = pd.read_csv(FILES["kpi"])

check(
    len(kpi) == 24,
    "KPI dataset must contain 24 rows",
)

check(
    not kpi.duplicated(
        ["vehicle", "period"]
    ).any(),
    "Duplicate vehicle-period rows in KPI dataset",
)

check(
    set(kpi["vehicle"]) == expected_vehicles,
    "KPI vehicle list does not match configuration",
)

check(
    kpi["vehicle"].str.fullmatch(
        ALIAS_PATTERN,
        na=False,
    ).all(),
    "Invalid vehicle alias in KPI dataset",
)

period_counts = kpi["period"].value_counts()

check(
    period_counts.get("before", 0) == 12,
    "KPI dataset must contain 12 Before rows",
)

check(
    period_counts.get("after", 0) == 12,
    "KPI dataset must contain 12 After rows",
)

kpi["analysis_start"] = (
    pd.to_datetime(
        kpi["analysis_start"],
        errors="coerce",
        utc=True,
    )
    .dt.tz_convert(KST)
)

kpi["analysis_end"] = (
    pd.to_datetime(
        kpi["analysis_end"],
        errors="coerce",
        utc=True,
    )
    .dt.tz_convert(KST)
)

check(
    kpi["analysis_start"].notna().all(),
    "Invalid KPI analysis_start timestamp",
)

check(
    kpi["analysis_end"].notna().all(),
    "Invalid KPI analysis_end timestamp",
)

outside_period_rows = 0

for row in kpi.itertuples(index=False):
    config = periods.loc[row.vehicle]

    expected_start = to_kst(
        config[f"{row.period}_start"]
    )

    expected_end = to_kst(
        config[
            f"{row.period}_end_exclusive"
        ]
    )

    if (
        row.analysis_start < expected_start
        or row.analysis_end >= expected_end
    ):
        outside_period_rows += 1

check(
    outside_period_rows == 0,
    "KPI rows outside configured periods found",
)

check_no_infinity("KPI", kpi)


component_config = {
    "FES": {
        "path": FILES["fes"],
        "before_score": "before_fes",
        "after_score": "after_fes",
        "before_raw": "before_fes_raw",
        "after_raw": "after_fes_raw",
    },
    "RES": {
        "path": FILES["res"],
        "before_score": "before_res",
        "after_score": "after_res",
        "before_raw": "before_res_raw",
        "after_raw": "after_res_raw",
    },
    "IES": {
        "path": FILES["ies"],
        "before_score": "before_ies",
        "after_score": "after_ies",
        "before_raw": "before_ies_raw",
        "after_raw": "after_ies_raw",
    },
    "DSS": {
        "path": FILES["dss"],
        "before_score": "before_dss",
        "after_score": "after_dss",
        "before_raw": "before_dss_raw",
        "after_raw": "after_dss_raw",
    },
}

component_results = []

for name, config in component_config.items():
    frame = pd.read_csv(config["path"])

    check(
        len(frame) == 12,
        f"{name}: expected 12 vehicle rows",
    )

    check(
        frame["vehicle"].nunique() == 12,
        f"{name}: expected 12 unique vehicles",
    )

    check(
        set(frame["vehicle"]) == expected_vehicles,
        f"{name}: vehicle list mismatch",
    )

    check_no_infinity(name, frame)

    for score_column in [
        config["before_score"],
        config["after_score"],
    ]:
        valid_scores = frame[
            score_column
        ].dropna()

        check(
            valid_scores.between(
                0,
                100,
                inclusive="both",
            ).all(),
            f"{name}: capped score outside 0–100",
        )

    valid_pair = frame[
        [
            config["before_score"],
            config["after_score"],
        ]
    ].notna().all(axis=1)

    before_saturation = (
        frame[config["before_raw"]].gt(100)
    ).sum()

    after_saturation = (
        frame[config["after_raw"]].gt(100)
    ).sum()

    component_results.append(
        {
            "component": name,
            "rows": len(frame),
            "valid_pairs": int(valid_pair.sum()),
            "missing_pairs": int(
                (~valid_pair).sum()
            ),
            "before_saturation": int(
                before_saturation
            ),
            "after_saturation": int(
                after_saturation
            ),
        }
    )


quality = pd.read_csv(FILES["quality"])

check(
    len(quality) == 240,
    "Data quality summary must contain 240 rows",
)

check(
    not quality.duplicated(
        ["vehicle", "period", "signal"]
    ).any(),
    "Duplicate data-quality rows found",
)

check(
    set(quality["vehicle"]) == expected_vehicles,
    "Data-quality vehicle list mismatch",
)

check(
    quality["outside_period_count"].sum() == 0,
    "Data-quality records outside periods found",
)

check_no_infinity("Data quality", quality)


comparison = pd.read_csv(FILES["comparison"])
comparison_summary = pd.read_csv(
    FILES["comparison_summary"]
)

check(
    len(comparison) == 24,
    "Legacy comparison must contain 24 rows",
)

check(
    len(comparison_summary) == 9,
    "Legacy comparison summary must contain 9 metrics",
)

check_no_infinity(
    "Legacy comparison",
    comparison,
)

check_no_infinity(
    "Legacy comparison summary",
    comparison_summary,
)


if errors:
    print("\nDAY 2 VALIDATION FAILED")

    for error in errors:
        print(f"- {error}")

    raise SystemExit(1)


print("\nDAY 2 VALIDATION PASSED")
print(f"KPI rows: {len(kpi)}")
print(f"Outside-period KPI rows: {outside_period_rows}")
print(f"Data-quality rows: {len(quality)}")
print(f"Legacy comparison rows: {len(comparison)}")

print("\nComponent availability and saturation")
print(
    pd.DataFrame(
        component_results
    ).to_string(index=False)
)

missing_signals = (
    quality.loc[
        ~quality["signal_present"].astype(bool)
    ]
    .groupby(["period", "signal"])
    .size()
    .reset_index(name="missing_vehicle_count")
)

print("\nMissing signal coverage")
print(
    missing_signals.to_string(index=False)
    if not missing_signals.empty
    else "None"
)