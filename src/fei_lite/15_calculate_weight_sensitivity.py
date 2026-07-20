from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path(
    "outputs/tables/component_index_method_detail_v2.csv"
)

DETAIL_OUTPUT_PATH = Path(
    "outputs/tables/fei_weight_sensitivity_detail_v2.csv"
)

SUMMARY_OUTPUT_PATH = Path(
    "outputs/tables/fei_weight_sensitivity_v2.csv"
)

COMPONENTS = ["FES", "RES", "IES", "DSS"]

WEIGHT_SCENARIOS = {
    "primary_50_20_20_10": {
        "FES": 0.50,
        "RES": 0.20,
        "IES": 0.20,
        "DSS": 0.10,
    },
    "legacy_40_25_20_15": {
        "FES": 0.40,
        "RES": 0.25,
        "IES": 0.20,
        "DSS": 0.15,
    },
    "equal_25_25_25_25": {
        "FES": 0.25,
        "RES": 0.25,
        "IES": 0.25,
        "DSS": 0.25,
    },
}

PRIMARY_SCENARIO = "primary_50_20_20_10"

MINIMUM_COMPONENT_COUNT = 3
STATUS_TOLERANCE = 0.1


def classify_change(change):
    if pd.isna(change):
        return "Missing"

    if abs(change) <= STATUS_TOLERANCE:
        return "Unchanged"

    if change > 0:
        return "Improved"

    return "Declined"


component_df = pd.read_csv(INPUT_PATH)

required_columns = {
    "vehicle",
    "component",
    "before_bounded_0_200",
    "after_bounded_0_200",
}

missing_columns = (
    required_columns - set(component_df.columns)
)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

if component_df.duplicated(
    ["vehicle", "component"]
).any():
    raise ValueError(
        "Duplicate vehicle-component rows found"
    )

vehicles = sorted(
    component_df["vehicle"].unique()
)

result_rows = []

for scenario, nominal_weights in (
    WEIGHT_SCENARIOS.items()
):
    for vehicle in vehicles:
        vehicle_df = (
            component_df[
                component_df["vehicle"] == vehicle
            ]
            .set_index("component")
            .reindex(COMPONENTS)
        )

        available = {}

        for component in COMPONENTS:
            before_value = vehicle_df.loc[
                component,
                "before_bounded_0_200",
            ]

            after_value = vehicle_df.loc[
                component,
                "after_bounded_0_200",
            ]

            available[component] = (
                pd.notna(before_value)
                and pd.notna(after_value)
            )

        available_components = [
            component
            for component in COMPONENTS
            if available[component]
        ]

        missing_components = [
            component
            for component in COMPONENTS
            if not available[component]
        ]

        valid_for_fei = (
            available.get("FES", False)
            and len(available_components)
            >= MINIMUM_COMPONENT_COUNT
        )

        effective_weights = {
            component: 0.0
            for component in COMPONENTS
        }

        before_fei = np.nan
        after_fei = np.nan

        if valid_for_fei:
            available_weight_total = sum(
                nominal_weights[component]
                for component in available_components
            )

            if available_weight_total <= 0:
                raise ValueError(
                    "Available weight total must be positive"
                )

            for component in available_components:
                effective_weights[component] = (
                    nominal_weights[component]
                    / available_weight_total
                )

            before_fei = sum(
                vehicle_df.loc[
                    component,
                    "before_bounded_0_200",
                ]
                * effective_weights[component]
                for component in available_components
            )

            after_fei = sum(
                vehicle_df.loc[
                    component,
                    "after_bounded_0_200",
                ]
                * effective_weights[component]
                for component in available_components
            )

        fei_change = (
            after_fei - before_fei
            if (
                pd.notna(before_fei)
                and pd.notna(after_fei)
            )
            else np.nan
        )

        fei_change_pct = (
            fei_change / before_fei * 100
            if (
                pd.notna(fei_change)
                and before_fei > 0
            )
            else np.nan
        )

        result_rows.append(
            {
                "weight_scenario": scenario,
                "vehicle": vehicle,
                "available_component_count":
                    len(available_components),
                "missing_components":
                    ",".join(missing_components),
                "valid_for_fei": valid_for_fei,
                "effective_fes_weight":
                    effective_weights["FES"],
                "effective_res_weight":
                    effective_weights["RES"],
                "effective_ies_weight":
                    effective_weights["IES"],
                "effective_dss_weight":
                    effective_weights["DSS"],
                "before_fei_lite": before_fei,
                "after_fei_lite": after_fei,
                "fei_absolute_change": fei_change,
                "fei_percentage_change":
                    fei_change_pct,
                "change_status":
                    classify_change(fei_change),
            }
        )

detail = pd.DataFrame(result_rows)

detail["after_rank"] = (
    detail.groupby("weight_scenario")[
        "after_fei_lite"
    ]
    .rank(
        ascending=False,
        method="dense",
    )
    .astype("Int64")
)

primary = detail[
    detail["weight_scenario"]
    == PRIMARY_SCENARIO
][
    [
        "vehicle",
        "after_fei_lite",
        "after_rank",
        "change_status",
    ]
].rename(
    columns={
        "after_fei_lite":
            "primary_after_fei_lite",
        "after_rank": "primary_after_rank",
        "change_status":
            "primary_change_status",
    }
)

summary_rows = []

for scenario in WEIGHT_SCENARIOS:
    scenario_df = detail[
        detail["weight_scenario"] == scenario
    ].copy()

    valid_df = scenario_df[
        scenario_df["valid_for_fei"]
    ].copy()

    fleet_before = valid_df[
        "before_fei_lite"
    ].mean()

    fleet_after = valid_df[
        "after_fei_lite"
    ].mean()

    fleet_absolute_change = (
        fleet_after - fleet_before
    )

    fleet_percentage_change = (
        fleet_absolute_change
        / fleet_before
        * 100
        if fleet_before > 0
        else np.nan
    )

    comparison = scenario_df.merge(
        primary,
        on="vehicle",
        how="inner",
    )

    valid_rank_comparison = comparison.dropna(
        subset=[
            "after_fei_lite",
            "primary_after_fei_lite",
        ]
    ).copy()

    if len(valid_rank_comparison) > 1:
        scenario_rank = valid_rank_comparison[
            "after_fei_lite"
        ].rank(ascending=False)

        primary_rank = valid_rank_comparison[
            "primary_after_fei_lite"
        ].rank(ascending=False)

        rank_correlation = scenario_rank.corr(
            primary_rank
        )
    else:
        rank_correlation = np.nan

    status_changed_count = int(
        (
            comparison["change_status"]
            != comparison[
                "primary_change_status"
            ]
        ).sum()
    )

    summary_rows.append(
        {
            "weight_scenario": scenario,
            "valid_vehicle_count":
                len(valid_df),
            "missing_vehicle_count":
                len(scenario_df) - len(valid_df),
            "fleet_avg_before_fei_lite":
                fleet_before,
            "fleet_avg_after_fei_lite":
                fleet_after,
            "fleet_absolute_change":
                fleet_absolute_change,
            "fleet_percentage_change":
                fleet_percentage_change,
            "mean_vehicle_percentage_change":
                valid_df[
                    "fei_percentage_change"
                ].mean(),
            "vehicles_improved": (
                scenario_df["change_status"]
                == "Improved"
            ).sum(),
            "vehicles_unchanged": (
                scenario_df["change_status"]
                == "Unchanged"
            ).sum(),
            "vehicles_declined": (
                scenario_df["change_status"]
                == "Declined"
            ).sum(),
            "vehicles_missing": (
                scenario_df["change_status"]
                == "Missing"
            ).sum(),
            "status_changed_vs_primary":
                status_changed_count,
            "after_rank_correlation_vs_primary":
                rank_correlation,
        }
    )

summary = pd.DataFrame(summary_rows)

DETAIL_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

SUMMARY_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

detail.to_csv(
    DETAIL_OUTPUT_PATH,
    index=False,
)

summary.to_csv(
    SUMMARY_OUTPUT_PATH,
    index=False,
)

print("Weight sensitivity analysis saved")
print(f"Detail: {DETAIL_OUTPUT_PATH}")
print(f"Summary: {SUMMARY_OUTPUT_PATH}")

print("\nSensitivity summary")
print(summary.to_string(index=False))

print("\nPrimary effective weights")
print(
    detail.loc[
        detail["weight_scenario"]
        == PRIMARY_SCENARIO,
        [
            "vehicle",
            "available_component_count",
            "missing_components",
            "effective_fes_weight",
            "effective_res_weight",
            "effective_ies_weight",
            "effective_dss_weight",
        ],
    ].to_string(index=False)
)