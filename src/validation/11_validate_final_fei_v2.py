from pathlib import Path
import hashlib

import numpy as np
import pandas as pd


KPI_PATH = Path(
    "data/processed/vehicle_kpi_dataset_v2.csv"
)

FEI_PATH = Path(
    "data/processed/vehicle_fei_scores_v2.csv"
)

SUMMARY_PATH = Path(
    "data/processed/fei_lite_summary_v2.csv"
)

QUALITY_PATH = Path(
    "data/processed/data_quality_summary.csv"
)

SENSITIVITY_PATH = Path(
    "outputs/tables/fei_weight_sensitivity_v2.csv"
)

MANIFEST_PATH = Path(
    "outputs/tables/final_v2_file_manifest.csv"
)

COMPONENTS = ["fes", "res", "ies", "dss"]
STATUS_TOLERANCE = 0.1

errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def check_no_infinity(name, frame):
    numeric = frame.select_dtypes(
        include=[np.number]
    )

    values = numeric.to_numpy(
        dtype=float,
        na_value=np.nan,
    )

    check(
        not np.isinf(values).any(),
        f"{name}: infinite value found",
    )


def classify_change(change):
    if pd.isna(change):
        return "Missing"

    if abs(change) <= STATUS_TOLERANCE:
        return "Unchanged"

    if change > 0:
        return "Improved"

    return "Declined"


required_paths = [
    KPI_PATH,
    FEI_PATH,
    SUMMARY_PATH,
    QUALITY_PATH,
    SENSITIVITY_PATH,
]

for path in required_paths:
    check(
        path.exists(),
        f"Missing required file: {path}",
    )

if errors:
    for error in errors:
        print(f"FAIL: {error}")

    raise SystemExit(1)


kpi = pd.read_csv(KPI_PATH)
fei = pd.read_csv(FEI_PATH)
summary = pd.read_csv(SUMMARY_PATH)
quality = pd.read_csv(QUALITY_PATH)
sensitivity = pd.read_csv(SENSITIVITY_PATH)


# KPI validation
check(
    len(kpi) == 24,
    "KPI V2 must contain 24 rows",
)

check(
    kpi["vehicle"].nunique() == 12,
    "KPI V2 must contain 12 vehicles",
)

check(
    not kpi.duplicated(
        ["vehicle", "period"]
    ).any(),
    "Duplicate vehicle-period KPI rows found",
)

period_counts = kpi["period"].value_counts()

check(
    period_counts.get("before", 0) == 12,
    "KPI V2 must contain 12 Before rows",
)

check(
    period_counts.get("after", 0) == 12,
    "KPI V2 must contain 12 After rows",
)

check(
    (
        kpi["calculation_version"]
        == "v2_time_weighted"
    ).all(),
    "Unexpected KPI calculation version",
)

check_no_infinity("KPI V2", kpi)


# FEI file validation
check(
    len(fei) == 12,
    "FEI V2 must contain 12 rows",
)

check(
    fei["vehicle"].nunique() == 12,
    "FEI V2 must contain 12 unique vehicles",
)

check(
    not fei["vehicle"].duplicated().any(),
    "Duplicate vehicle rows in FEI V2",
)

valid_for_fei = (
    fei["valid_for_fei"]
    .astype(str)
    .str.lower()
    .eq("true")
)

check(
    valid_for_fei.sum() == 12,
    "All 12 vehicles should have valid FEI V2",
)

for component in COMPONENTS:
    for period in ["before", "after"]:
        column = f"{period}_{component}_index"

        valid_scores = fei[column].dropna()

        check(
            valid_scores.between(
                0,
                200,
                inclusive="both",
            ).all(),
            f"{column} is outside 0–200",
        )

        check(
            not valid_scores.eq(0).any(),
            f"{column} contains 0-point saturation",
        )

        check(
            not valid_scores.eq(200).any(),
            f"{column} contains 200-point saturation",
        )


weight_columns = [
    "effective_fes_weight",
    "effective_res_weight",
    "effective_ies_weight",
    "effective_dss_weight",
]

weight_sum = fei[weight_columns].sum(axis=1)

check(
    np.allclose(
        weight_sum,
        1.0,
        atol=1e-9,
    ),
    "Effective weights do not sum to 1",
)

calculated_before = pd.Series(
    0.0,
    index=fei.index,
)

calculated_after = pd.Series(
    0.0,
    index=fei.index,
)

for component in COMPONENTS:
    calculated_before += (
        fei[f"before_{component}_index"]
        .fillna(0)
        * fei[f"effective_{component}_weight"]
    )

    calculated_after += (
        fei[f"after_{component}_index"]
        .fillna(0)
        * fei[f"effective_{component}_weight"]
    )

check(
    np.allclose(
        calculated_before,
        fei["before_fei_lite"],
        atol=1e-9,
    ),
    "Before FEI weighted calculation mismatch",
)

check(
    np.allclose(
        calculated_after,
        fei["after_fei_lite"],
        atol=1e-9,
    ),
    "After FEI weighted calculation mismatch",
)

calculated_change = (
    fei["after_fei_lite"]
    - fei["before_fei_lite"]
)

check(
    np.allclose(
        calculated_change,
        fei["fei_absolute_change"],
        atol=1e-9,
    ),
    "FEI absolute change mismatch",
)

calculated_percentage = (
    calculated_change
    / fei["before_fei_lite"]
    * 100
)

check(
    np.allclose(
        calculated_percentage,
        fei["fei_percentage_change"],
        atol=1e-9,
    ),
    "FEI percentage change mismatch",
)

calculated_status = calculated_change.apply(
    classify_change
)

check(
    calculated_status.equals(
        fei["change_status"]
    ),
    "FEI status classification mismatch",
)

calculated_rank = (
    fei["after_fei_lite"]
    .rank(
        ascending=False,
        method="dense",
    )
    .astype("Int64")
)

stored_rank = fei["after_rank"].astype("Int64")

check(
    calculated_rank.equals(stored_rank),
    "After FEI ranking mismatch",
)

check_no_infinity("FEI V2", fei)


# Missing-component validation
ldv_07 = fei[
    fei["vehicle"] == "LDV_07"
]

check(
    len(ldv_07) == 1,
    "LDV_07 result not found",
)

if len(ldv_07) == 1:
    row = ldv_07.iloc[0]

    check(
        row["missing_components"] == "DSS",
        "LDV_07 missing component must be DSS",
    )

    check(
        row["available_component_count"] == 3,
        "LDV_07 must have 3 available components",
    )

    check(
        np.isclose(
            row["effective_fes_weight"],
            0.50 / 0.90,
        ),
        "LDV_07 FES reweighting mismatch",
    )

    check(
        np.isclose(
            row["effective_res_weight"],
            0.20 / 0.90,
        ),
        "LDV_07 RES reweighting mismatch",
    )

    check(
        np.isclose(
            row["effective_ies_weight"],
            0.20 / 0.90,
        ),
        "LDV_07 IES reweighting mismatch",
    )

    check(
        np.isclose(
            row["effective_dss_weight"],
            0.0,
        ),
        "LDV_07 DSS weight must be zero",
    )


# Summary validation
summary_values = summary.set_index(
    "metric"
)["value"]


def summary_float(metric):
    return float(summary_values.loc[metric])


fleet_before = fei.loc[
    valid_for_fei,
    "before_fei_lite",
].mean()

fleet_after = fei.loc[
    valid_for_fei,
    "after_fei_lite",
].mean()

fleet_change = fleet_after - fleet_before

fleet_change_pct = (
    fleet_change / fleet_before * 100
)

check(
    np.isclose(
        summary_float(
            "fleet_avg_before_fei_lite"
        ),
        fleet_before,
    ),
    "Fleet Before average mismatch",
)

check(
    np.isclose(
        summary_float(
            "fleet_avg_after_fei_lite"
        ),
        fleet_after,
    ),
    "Fleet After average mismatch",
)

check(
    np.isclose(
        summary_float(
            "fleet_absolute_change"
        ),
        fleet_change,
    ),
    "Fleet absolute change mismatch",
)

check(
    np.isclose(
        summary_float(
            "fleet_percentage_change"
        ),
        fleet_change_pct,
    ),
    "Fleet percentage change mismatch",
)

status_counts = fei[
    "change_status"
].value_counts()

for status, metric in [
    ("Improved", "vehicles_improved"),
    ("Unchanged", "vehicles_unchanged"),
    ("Declined", "vehicles_declined"),
    ("Missing", "vehicles_missing"),
]:
    check(
        summary_float(metric)
        == status_counts.get(status, 0),
        f"{status} vehicle count mismatch",
    )


# Data-quality validation
check(
    len(quality) == 240,
    "Data-quality summary must contain 240 rows",
)

check(
    quality["outside_period_count"].sum() == 0,
    "Outside-period data found",
)

check_no_infinity("Data quality", quality)


# Sensitivity validation
check(
    sensitivity[
        "weight_scenario"
    ].nunique() == 3,
    "Expected three weight scenarios",
)

primary = sensitivity[
    sensitivity["weight_scenario"]
    == "primary_50_20_20_10"
]

check(
    len(primary) == 1,
    "Primary sensitivity summary missing",
)

if len(primary) == 1:
    primary_row = primary.iloc[0]

    check(
        np.isclose(
            primary_row[
                "fleet_avg_before_fei_lite"
            ],
            fleet_before,
        ),
        "Primary sensitivity Before mismatch",
    )

    check(
        np.isclose(
            primary_row[
                "fleet_avg_after_fei_lite"
            ],
            fleet_after,
        ),
        "Primary sensitivity After mismatch",
    )


if errors:
    print("\nDAY 3 FINAL VALIDATION FAILED")

    for error in errors:
        print(f"- {error}")

    raise SystemExit(1)


# Freeze file versions with hashes.
manifest_rows = []

for path in [
    KPI_PATH,
    FEI_PATH,
    SUMMARY_PATH,
    QUALITY_PATH,
]:
    file_hash = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

    frame = pd.read_csv(path)

    manifest_rows.append(
        {
            "file": path.name,
            "path": str(path),
            "rows": len(frame),
            "columns": len(frame.columns),
            "sha256": file_hash,
        }
    )

manifest = pd.DataFrame(manifest_rows)

MANIFEST_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

manifest.to_csv(
    MANIFEST_PATH,
    index=False,
)

print("\nDAY 3 FINAL VALIDATION PASSED")
print(f"KPI rows: {len(kpi)}")
print(f"FEI vehicles: {len(fei)}")
print(f"Data-quality rows: {len(quality)}")
print(f"Manifest: {MANIFEST_PATH}")

print("\nFrozen fleet results")
print(
    pd.DataFrame(
        [
            {
                "fleet_before": fleet_before,
                "fleet_after": fleet_after,
                "absolute_change": fleet_change,
                "percentage_change":
                    fleet_change_pct,
                "improved":
                    status_counts.get(
                        "Improved",
                        0,
                    ),
                "unchanged":
                    status_counts.get(
                        "Unchanged",
                        0,
                    ),
                "declined":
                    status_counts.get(
                        "Declined",
                        0,
                    ),
                "missing":
                    status_counts.get(
                        "Missing",
                        0,
                    ),
            }
        ]
    ).to_string(index=False)
)

print("\nFinal file manifest")
print(manifest.to_string(index=False))