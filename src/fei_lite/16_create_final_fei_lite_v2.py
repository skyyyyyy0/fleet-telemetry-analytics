from pathlib import Path

import numpy as np
import pandas as pd


KPI_INPUT_PATH = Path(
    "data/processed/vehicle_kpi_dataset.csv"
)

COMPONENT_INPUT_PATH = Path(
    "outputs/tables/component_index_method_detail_v2.csv"
)

SENSITIVITY_INPUT_PATH = Path(
    "outputs/tables/fei_weight_sensitivity_detail_v2.csv"
)

QUALITY_PATH = Path(
    "data/processed/data_quality_summary.csv"
)

KPI_OUTPUT_PATH = Path(
    "data/processed/vehicle_kpi_dataset_v2.csv"
)

FEI_OUTPUT_PATH = Path(
    "data/processed/vehicle_fei_scores_v2.csv"
)

SUMMARY_OUTPUT_PATH = Path(
    "data/processed/fei_lite_summary_v2.csv"
)

PRIMARY_SCENARIO = "primary_50_20_20_10"
INDEX_METHOD = "bounded_0_200"
STATUS_TOLERANCE = 0.1

COMPONENTS = ["FES", "RES", "IES", "DSS"]

NOMINAL_WEIGHTS = {
    "FES": 0.50,
    "RES": 0.20,
    "IES": 0.20,
    "DSS": 0.10,
}


def classify_change(change):
    if pd.isna(change):
        return "Missing"

    if abs(change) <= STATUS_TOLERANCE:
        return "Unchanged"

    if change > 0:
        return "Improved"

    return "Declined"


def get_vehicle_class(vehicle):
    vehicle = str(vehicle)

    if vehicle.startswith("HDV_"):
        return "Heavy-Duty"

    if vehicle.startswith("LDV_"):
        return "Light-Duty"

    return "Unknown"


for required_path in [
    KPI_INPUT_PATH,
    COMPONENT_INPUT_PATH,
    SENSITIVITY_INPUT_PATH,
    QUALITY_PATH,
]:
    if not required_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {required_path}"
        )


kpi = pd.read_csv(KPI_INPUT_PATH)

if len(kpi) != 24:
    raise ValueError(
        "KPI dataset must contain 24 rows"
    )

if kpi.duplicated(
    ["vehicle", "period"]
).any():
    raise ValueError(
        "Duplicate vehicle-period KPI rows found"
    )

if kpi["vehicle"].nunique() != 12:
    raise ValueError(
        "KPI dataset must contain 12 vehicles"
    )

kpi_v2 = kpi.copy()

kpi_v2.insert(
    0,
    "calculation_version",
    "v2_time_weighted",
)

component_detail = pd.read_csv(
    COMPONENT_INPUT_PATH
)

if component_detail.duplicated(
    ["vehicle", "component"]
).any():
    raise ValueError(
        "Duplicate vehicle-component rows found"
    )

component_wide = pd.DataFrame(
    {
        "vehicle": sorted(
            component_detail["vehicle"].unique()
        )
    }
)

for component in COMPONENTS:
    prefix = component.lower()

    component_data = component_detail[
        component_detail["component"] == component
    ][
        [
            "vehicle",
            "direction",
            "baseline_scope",
            "before_metric",
            "after_metric",
            "baseline",
            "before_bounded_0_200",
            "after_bounded_0_200",
        ]
    ].rename(
        columns={
            "direction":
                f"{prefix}_direction",
            "baseline_scope":
                f"{prefix}_baseline_scope",
            "before_metric":
                f"before_{prefix}_metric",
            "after_metric":
                f"after_{prefix}_metric",
            "baseline":
                f"{prefix}_baseline",
            "before_bounded_0_200":
                f"before_{prefix}_index",
            "after_bounded_0_200":
                f"after_{prefix}_index",
        }
    )

    component_wide = component_wide.merge(
        component_data,
        on="vehicle",
        how="left",
        validate="one_to_one",
    )


sensitivity = pd.read_csv(
    SENSITIVITY_INPUT_PATH
)

primary = sensitivity[
    sensitivity["weight_scenario"]
    == PRIMARY_SCENARIO
].copy()

if len(primary) != 12:
    raise ValueError(
        "Primary sensitivity result must contain 12 vehicles"
    )

primary = primary[
    [
        "vehicle",
        "weight_scenario",
        "available_component_count",
        "missing_components",
        "valid_for_fei",
        "effective_fes_weight",
        "effective_res_weight",
        "effective_ies_weight",
        "effective_dss_weight",
        "before_fei_lite",
        "after_fei_lite",
    ]
].rename(
    columns={
        "weight_scenario":
            "final_weight_scenario"
    }
)

primary["missing_components"] = (
    primary["missing_components"]
    .fillna("")
)

fei = primary.merge(
    component_wide,
    on="vehicle",
    how="left",
    validate="one_to_one",
)

fei["vehicle_class"] = fei[
    "vehicle"
].apply(get_vehicle_class)

effective_weight_columns = [
    "effective_fes_weight",
    "effective_res_weight",
    "effective_ies_weight",
    "effective_dss_weight",
]

fei["effective_weight_sum"] = fei[
    effective_weight_columns
].sum(axis=1)

valid_weight_rows = fei["valid_for_fei"].astype(bool)

if not np.allclose(
    fei.loc[
        valid_weight_rows,
        "effective_weight_sum",
    ],
    1.0,
    atol=1e-9,
):
    raise ValueError(
        "Effective FEI weights do not sum to 1"
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
    prefix = component.lower()

    calculated_before += (
        fei[f"before_{prefix}_index"]
        .fillna(0)
        * fei[f"effective_{prefix}_weight"]
    )

    calculated_after += (
        fei[f"after_{prefix}_index"]
        .fillna(0)
        * fei[f"effective_{prefix}_weight"]
    )

calculated_before = calculated_before.where(
    valid_weight_rows
)

calculated_after = calculated_after.where(
    valid_weight_rows
)

if not np.allclose(
    calculated_before.dropna(),
    fei.loc[
        calculated_before.notna(),
        "before_fei_lite",
    ],
    atol=1e-9,
):
    raise ValueError(
        "Before FEI recalculation mismatch"
    )

if not np.allclose(
    calculated_after.dropna(),
    fei.loc[
        calculated_after.notna(),
        "after_fei_lite",
    ],
    atol=1e-9,
):
    raise ValueError(
        "After FEI recalculation mismatch"
    )

fei["before_fei_lite"] = calculated_before
fei["after_fei_lite"] = calculated_after

fei["fei_absolute_change"] = (
    fei["after_fei_lite"]
    - fei["before_fei_lite"]
)

before_denominator = fei[
    "before_fei_lite"
].where(
    fei["before_fei_lite"] > 0
)

fei["fei_percentage_change"] = (
    fei["fei_absolute_change"]
    / before_denominator
    * 100
)

fei["change_status"] = fei[
    "fei_absolute_change"
].apply(classify_change)

fei["after_rank"] = (
    fei["after_fei_lite"]
    .rank(
        ascending=False,
        method="dense",
    )
    .astype("Int64")
)

numeric_columns = fei.select_dtypes(
    include=[np.number]
)

numeric_values = numeric_columns.to_numpy(
    dtype=float,
    na_value=np.nan,
)

if np.isinf(numeric_values).any():
    raise ValueError(
        "Infinite value found in final FEI dataset"
    )


column_order = [
    "vehicle",
    "vehicle_class",
    "final_weight_scenario",
    "available_component_count",
    "missing_components",
    "valid_for_fei",
]

for component in COMPONENTS:
    prefix = component.lower()

    column_order.extend(
        [
            f"{prefix}_direction",
            f"{prefix}_baseline_scope",
            f"{prefix}_baseline",
            f"before_{prefix}_metric",
            f"after_{prefix}_metric",
            f"before_{prefix}_index",
            f"after_{prefix}_index",
        ]
    )

column_order.extend(
    [
        "effective_fes_weight",
        "effective_res_weight",
        "effective_ies_weight",
        "effective_dss_weight",
        "effective_weight_sum",
        "before_fei_lite",
        "after_fei_lite",
        "fei_absolute_change",
        "fei_percentage_change",
        "change_status",
        "after_rank",
    ]
)

fei = fei[column_order].sort_values(
    "after_rank"
).reset_index(drop=True)


valid_fei = fei[
    fei["valid_for_fei"].astype(bool)
].copy()

fleet_before = valid_fei[
    "before_fei_lite"
].mean()

fleet_after = valid_fei[
    "after_fei_lite"
].mean()

fleet_absolute_change = (
    fleet_after - fleet_before
)

fleet_percentage_change = (
    fleet_absolute_change
    / fleet_before
    * 100
)

summary_rows = [
    {
        "metric": "fei_lite_version",
        "value": "v2",
    },
    {
        "metric": "component_index_method",
        "value": INDEX_METHOD,
    },
    {
        "metric": "component_index_range",
        "value": "0-200",
    },
    {
        "metric": "baseline_reference",
        "value": "100",
    },
    {
        "metric": "final_weight_scenario",
        "value": PRIMARY_SCENARIO,
    },
    {
        "metric": "nominal_fes_weight",
        "value": NOMINAL_WEIGHTS["FES"],
    },
    {
        "metric": "nominal_res_weight",
        "value": NOMINAL_WEIGHTS["RES"],
    },
    {
        "metric": "nominal_ies_weight",
        "value": NOMINAL_WEIGHTS["IES"],
    },
    {
        "metric": "nominal_dss_weight",
        "value": NOMINAL_WEIGHTS["DSS"],
    },
    {
        "metric": "status_tolerance_points",
        "value": STATUS_TOLERANCE,
    },
    {
        "metric": "fleet_average_method",
        "value":
            "equal_vehicle_mean_across_valid_vehicles",
    },
    {
        "metric": "valid_vehicle_count",
        "value": len(valid_fei),
    },
    {
        "metric": "missing_vehicle_count",
        "value": len(fei) - len(valid_fei),
    },
    {
        "metric": "fleet_avg_before_fei_lite",
        "value": fleet_before,
    },
    {
        "metric": "fleet_avg_after_fei_lite",
        "value": fleet_after,
    },
    {
        "metric": "fleet_absolute_change",
        "value": fleet_absolute_change,
    },
    {
        "metric": "fleet_percentage_change",
        "value": fleet_percentage_change,
    },
    {
        "metric": "mean_vehicle_percentage_change",
        "value": valid_fei[
            "fei_percentage_change"
        ].mean(),
    },
    {
        "metric": "vehicles_improved",
        "value": (
            fei["change_status"] == "Improved"
        ).sum(),
    },
    {
        "metric": "vehicles_unchanged",
        "value": (
            fei["change_status"] == "Unchanged"
        ).sum(),
    },
    {
        "metric": "vehicles_declined",
        "value": (
            fei["change_status"] == "Declined"
        ).sum(),
    },
    {
        "metric": "vehicles_missing",
        "value": (
            fei["change_status"] == "Missing"
        ).sum(),
    },
    {
        "metric": "top_vehicle_after_fei",
        "value": valid_fei.iloc[0]["vehicle"],
    },
    {
        "metric": "top_vehicle_after_fei_value",
        "value": valid_fei.iloc[0][
            "after_fei_lite"
        ],
    },
    {
        "metric": "bottom_vehicle_after_fei",
        "value": valid_fei.iloc[-1]["vehicle"],
    },
    {
        "metric": "bottom_vehicle_after_fei_value",
        "value": valid_fei.iloc[-1][
            "after_fei_lite"
        ],
    },
]

for vehicle_class, class_df in (
    valid_fei.groupby("vehicle_class")
):
    class_prefix = (
        "heavy_duty"
        if vehicle_class == "Heavy-Duty"
        else "light_duty"
    )

    class_before = class_df[
        "before_fei_lite"
    ].mean()

    class_after = class_df[
        "after_fei_lite"
    ].mean()

    summary_rows.extend(
        [
            {
                "metric":
                    f"{class_prefix}_vehicle_count",
                "value": len(class_df),
            },
            {
                "metric":
                    f"{class_prefix}_avg_before_fei",
                "value": class_before,
            },
            {
                "metric":
                    f"{class_prefix}_avg_after_fei",
                "value": class_after,
            },
            {
                "metric":
                    f"{class_prefix}_absolute_change",
                "value":
                    class_after - class_before,
            },
        ]
    )

summary = pd.DataFrame(summary_rows)

KPI_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

FEI_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

SUMMARY_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

kpi_v2.to_csv(
    KPI_OUTPUT_PATH,
    index=False,
)

fei.to_csv(
    FEI_OUTPUT_PATH,
    index=False,
)

summary.to_csv(
    SUMMARY_OUTPUT_PATH,
    index=False,
)

print("Final FEI-Lite V2 files saved")
print(f"KPI: {KPI_OUTPUT_PATH}")
print(f"FEI: {FEI_OUTPUT_PATH}")
print(f"Summary: {SUMMARY_OUTPUT_PATH}")
print(f"Data quality: {QUALITY_PATH}")

print("\nFinal fleet results")
print(
    summary[
        summary["metric"].isin(
            [
                "fleet_avg_before_fei_lite",
                "fleet_avg_after_fei_lite",
                "fleet_absolute_change",
                "fleet_percentage_change",
                "vehicles_improved",
                "vehicles_unchanged",
                "vehicles_declined",
                "vehicles_missing",
            ]
        )
    ].to_string(index=False)
)

print("\nFinal vehicle results")
print(
    fei[
        [
            "after_rank",
            "vehicle",
            "before_fei_lite",
            "after_fei_lite",
            "fei_absolute_change",
            "fei_percentage_change",
            "change_status",
            "missing_components",
        ]
    ].to_string(index=False)
)