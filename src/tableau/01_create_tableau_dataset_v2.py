from pathlib import Path

import numpy as np
import pandas as pd


FEI_PATH = Path(
    "data/processed/vehicle_fei_scores_v2.csv"
)

PERIOD_PATH = Path(
    "config/analysis_periods.csv"
)

OUTPUT_PATH = Path(
    "data/processed/tableau_fei_dashboard_v2.csv"
)


fei = pd.read_csv(FEI_PATH)
periods = pd.read_csv(PERIOD_PATH)

if len(fei) != 12:
    raise ValueError(
        "FEI V2 dataset must contain 12 vehicles"
    )

if fei["vehicle"].duplicated().any():
    raise ValueError(
        "Duplicate vehicles in FEI V2 dataset"
    )

if periods["vehicle_id"].duplicated().any():
    raise ValueError(
        "Duplicate vehicles in analysis periods"
    )

periods = periods.rename(
    columns={"vehicle_id": "vehicle"}
)

tableau = fei.merge(
    periods,
    on="vehicle",
    how="left",
    validate="one_to_one",
)

if tableau["install_date"].isna().any():
    raise ValueError(
        "Missing analysis period after merge"
    )


# Existing Tableau-compatible component names.
tableau["before_fes"] = tableau[
    "before_fes_index"
]

tableau["after_fes"] = tableau[
    "after_fes_index"
]

tableau["fes_change"] = (
    tableau["after_fes"]
    - tableau["before_fes"]
)

tableau["before_res"] = tableau[
    "before_res_index"
]

tableau["after_res"] = tableau[
    "after_res_index"
]

tableau["res_change"] = (
    tableau["after_res"]
    - tableau["before_res"]
)

tableau["before_ies"] = tableau[
    "before_ies_index"
]

tableau["after_ies"] = tableau[
    "after_ies_index"
]

tableau["ies_change"] = (
    tableau["after_ies"]
    - tableau["before_ies"]
)

tableau["before_dss"] = tableau[
    "before_dss_index"
]

tableau["after_dss"] = tableau[
    "after_dss_index"
]

tableau["dss_change"] = (
    tableau["after_dss"]
    - tableau["before_dss"]
)

tableau["fei_change"] = tableau[
    "fei_absolute_change"
]

tableau["fei_change_pct"] = tableau[
    "fei_percentage_change"
]

tableau["improved"] = (
    tableau["change_status"] == "Improved"
)

tableau["unchanged"] = (
    tableau["change_status"] == "Unchanged"
)

tableau["declined"] = (
    tableau["change_status"] == "Declined"
)

tableau["missing"] = (
    tableau["change_status"] == "Missing"
)

tableau["rank"] = tableau["after_rank"]


# Actual KPI changes for dashboard tooltips.
before_fe_denominator = tableau[
    "before_fes_metric"
].where(
    tableau["before_fes_metric"] > 0
)

tableau["fuel_efficiency_change_pct"] = (
    (
        tableau["after_fes_metric"]
        - tableau["before_fes_metric"]
    )
    / before_fe_denominator
    * 100
)

tableau["rpm_efficiency_change_pp"] = (
    tableau["after_res_metric"]
    - tableau["before_res_metric"]
) * 100

tableau["idle_ratio_change_pp"] = (
    tableau["after_ies_metric"]
    - tableau["before_ies_metric"]
) * 100

before_dss_denominator = tableau[
    "before_dss_metric"
].where(
    tableau["before_dss_metric"] > 0
)

tableau["driving_events_change_pct"] = (
    (
        tableau["after_dss_metric"]
        - tableau["before_dss_metric"]
    )
    / before_dss_denominator
    * 100
)


# Analysis-period labels.
tableau["before_period_label"] = (
    tableau["before_start"].astype(str)
    + " ≤ t < "
    + tableau[
        "before_end_exclusive"
    ].astype(str)
    + " KST"
)

tableau["after_period_label"] = (
    tableau["after_start"].astype(str)
    + " ≤ t < "
    + tableau[
        "after_end_exclusive"
    ].astype(str)
    + " KST"
)

tableau["analysis_period_display"] = (
    "Before: "
    + tableau["before_period_label"]
    + " | After: "
    + tableau["after_period_label"]
)


# FEI methodology metadata.
tableau["data_source_version"] = (
    "FEI-Lite V2"
)

tableau["component_index_method"] = (
    "Bounded 0–200 Index"
)

tableau["index_reference"] = (
    "100 = Before baseline"
)

tableau["nominal_fes_weight"] = 0.50
tableau["nominal_res_weight"] = 0.20
tableau["nominal_ies_weight"] = 0.20
tableau["nominal_dss_weight"] = 0.10

tableau["weight_reallocated"] = (
    tableau["available_component_count"] < 4
)

tableau["dss_available"] = (
    tableau["before_dss_index"].notna()
    & tableau["after_dss_index"].notna()
)


# Fleet-level constants for KPI cards.
fleet_before = tableau[
    "before_fei_lite"
].mean()

fleet_after = tableau[
    "after_fei_lite"
].mean()

fleet_change = (
    fleet_after - fleet_before
)

fleet_change_pct = (
    fleet_change / fleet_before * 100
)

tableau["fleet_avg_before_fei_lite"] = (
    fleet_before
)

tableau["fleet_avg_after_fei_lite"] = (
    fleet_after
)

tableau["fleet_absolute_change"] = (
    fleet_change
)

tableau["fleet_percentage_change"] = (
    fleet_change_pct
)

tableau["fleet_improved_count"] = (
    tableau["improved"].sum()
)

tableau["fleet_unchanged_count"] = (
    tableau["unchanged"].sum()
)

tableau["fleet_declined_count"] = (
    tableau["declined"].sum()
)

tableau["fleet_missing_count"] = (
    tableau["missing"].sum()
)

status_order = {
    "Improved": 1,
    "Unchanged": 2,
    "Declined": 3,
    "Missing": 4,
}

tableau["change_status_order"] = (
    tableau["change_status"].map(
        status_order
    )
)


legacy_columns = [
    "vehicle",
    "before_fes",
    "after_fes",
    "fes_change",
    "before_res",
    "after_res",
    "res_change",
    "before_ies",
    "after_ies",
    "ies_change",
    "before_dss",
    "after_dss",
    "dss_change",
    "before_fei_lite",
    "after_fei_lite",
    "fei_change",
    "fei_change_pct",
    "improved",
    "rank",
]

remaining_columns = [
    column
    for column in tableau.columns
    if column not in legacy_columns
]

tableau = tableau[
    legacy_columns + remaining_columns
]

numeric = tableau.select_dtypes(
    include=[np.number]
)

numeric_values = numeric.to_numpy(
    dtype=float,
    na_value=np.nan,
)

if np.isinf(numeric_values).any():
    raise ValueError(
        "Infinite value found in Tableau dataset"
    )

if not tableau["vehicle"].str.fullmatch(
    r"(?:HDV|LDV)_\d{2}",
    na=False,
).all():
    raise ValueError(
        "Invalid public vehicle alias found"
    )

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

tableau.to_csv(
    OUTPUT_PATH,
    index=False,
)

print("Tableau V2 dataset saved")
print(f"Output: {OUTPUT_PATH}")
print(f"Rows: {len(tableau)}")
print(f"Columns: {len(tableau.columns)}")

print("\nFleet KPI values")
print(
    {
        "before": round(fleet_before, 6),
        "after": round(fleet_after, 6),
        "absolute_change":
            round(fleet_change, 6),
        "percentage_change":
            round(fleet_change_pct, 6),
        "improved":
            int(tableau["improved"].sum()),
        "unchanged":
            int(tableau["unchanged"].sum()),
        "declined":
            int(tableau["declined"].sum()),
        "missing":
            int(tableau["missing"].sum()),
    }
)

print("\nPeriod groups")
print(
    tableau[
        [
            "install_date",
            "before_period_label",
            "after_period_label",
        ]
    ]
    .drop_duplicates()
    .to_string(index=False)
)