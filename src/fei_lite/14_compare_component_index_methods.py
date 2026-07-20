from pathlib import Path

import numpy as np
import pandas as pd


FES_PATH = Path("data/processed/fes_scores.csv")
RES_PATH = Path("data/processed/res_scores.csv")
IES_PATH = Path("data/processed/ies_scores.csv")
DSS_PATH = Path("data/processed/dss_scores.csv")

DETAIL_PATH = Path(
    "outputs/tables/component_index_method_detail_v2.csv"
)

SUMMARY_PATH = Path(
    "outputs/tables/component_index_method_comparison_v2.csv"
)

TOLERANCE = 1e-9


def bounded_higher(metric, baseline):
    denominator = metric + baseline

    return (
        200
        * metric
        / denominator.where(denominator > 0)
    )


def bounded_lower(metric, baseline):
    denominator = metric + baseline

    return (
        200
        * baseline
        / denominator.where(denominator > 0)
    )


def create_component_frame(
    frame,
    component,
    direction,
    before_metric,
    after_metric,
    baseline,
    baseline_scope,
    before_raw,
    after_raw,
    before_capped,
    after_capped,
):
    result = pd.DataFrame(
        {
            "vehicle": frame["vehicle"],
            "component": component,
            "direction": direction,
            "baseline_scope": baseline_scope,
            "before_metric": frame[before_metric],
            "after_metric": frame[after_metric],
            "baseline": baseline,
            "before_current_capped":
                frame[before_capped],
            "after_current_capped":
                frame[after_capped],
            "before_raw_ratio": frame[before_raw],
            "after_raw_ratio": frame[after_raw],
        }
    )

    if direction == "higher":
        result["directional_metric_change"] = (
            result["after_metric"]
            - result["before_metric"]
        )

        result["before_bounded_0_200"] = (
            bounded_higher(
                result["before_metric"],
                result["baseline"],
            )
        )

        result["after_bounded_0_200"] = (
            bounded_higher(
                result["after_metric"],
                result["baseline"],
            )
        )
    else:
        result["directional_metric_change"] = (
            result["before_metric"]
            - result["after_metric"]
        )

        result["before_bounded_0_200"] = (
            bounded_lower(
                result["before_metric"],
                result["baseline"],
            )
        )

        result["after_bounded_0_200"] = (
            bounded_lower(
                result["after_metric"],
                result["baseline"],
            )
        )

    return result


fes = pd.read_csv(FES_PATH)
res = pd.read_csv(RES_PATH)
ies = pd.read_csv(IES_PATH)
dss = pd.read_csv(DSS_PATH)

res_baseline = res[
    "before_rpm_efficiency_ratio"
].median()

ies_baseline = ies[
    "before_idle_ratio"
].median()

dss_baseline = dss.loc[
    dss["before_driving_events_per_100km"] > 0,
    "before_driving_events_per_100km",
].median()

component_frames = [
    create_component_frame(
        frame=fes,
        component="FES",
        direction="higher",
        before_metric=
            "before_fuel_efficiency_km_l",
        after_metric=
            "after_fuel_efficiency_km_l",
        baseline=fes["class_before_median_fe"],
        baseline_scope="vehicle_class_before_median",
        before_raw="before_fes_raw",
        after_raw="after_fes_raw",
        before_capped="before_fes",
        after_capped="after_fes",
    ),
    create_component_frame(
        frame=res,
        component="RES",
        direction="higher",
        before_metric=
            "before_rpm_efficiency_ratio",
        after_metric=
            "after_rpm_efficiency_ratio",
        baseline=res_baseline,
        baseline_scope="fleet_before_median",
        before_raw="before_res_raw",
        after_raw="after_res_raw",
        before_capped="before_res",
        after_capped="after_res",
    ),
    create_component_frame(
        frame=ies,
        component="IES",
        direction="lower",
        before_metric="before_idle_ratio",
        after_metric="after_idle_ratio",
        baseline=ies_baseline,
        baseline_scope="fleet_before_median",
        before_raw="before_ies_raw",
        after_raw="after_ies_raw",
        before_capped="before_ies",
        after_capped="after_ies",
    ),
    create_component_frame(
        frame=dss,
        component="DSS",
        direction="lower",
        before_metric=
            "before_driving_events_per_100km",
        after_metric=
            "after_driving_events_per_100km",
        baseline=dss_baseline,
        baseline_scope="fleet_before_positive_median",
        before_raw="before_dss_raw",
        after_raw="after_dss_raw",
        before_capped="before_dss",
        after_capped="after_dss",
    ),
]

detail = pd.concat(
    component_frames,
    ignore_index=True,
)

detail = detail.replace(
    [np.inf, -np.inf],
    np.nan,
)

methods = {
    "current_capped": (
        "before_current_capped",
        "after_current_capped",
    ),
    "raw_ratio": (
        "before_raw_ratio",
        "after_raw_ratio",
    ),
    "bounded_0_200": (
        "before_bounded_0_200",
        "after_bounded_0_200",
    ),
}

summary_rows = []

for component in [
    "FES",
    "RES",
    "IES",
    "DSS",
]:
    component_df = detail[
        detail["component"] == component
    ].copy()

    for method, columns in methods.items():
        before_column, after_column = columns

        valid = component_df.dropna(
            subset=[
                "before_metric",
                "after_metric",
                before_column,
                after_column,
            ]
        ).copy()

        valid["index_change"] = (
            valid[after_column]
            - valid[before_column]
        )

        metric_changed = (
            valid[
                "directional_metric_change"
            ].abs() > TOLERANCE
        )

        masked_change = (
            metric_changed
            & valid["index_change"].abs().le(
                TOLERANCE
            )
        )

        direction_conflict = (
            valid["directional_metric_change"]
            * valid["index_change"]
            < -TOLERANCE
        )

        fleet_metric_direction = valid[
            "directional_metric_change"
        ].mean()

        fleet_index_change = valid[
            "index_change"
        ].mean()

        if (
            abs(fleet_metric_direction)
            <= TOLERANCE
            and abs(fleet_index_change)
            <= TOLERANCE
        ):
            fleet_direction_match = True
        else:
            fleet_direction_match = (
                np.sign(fleet_metric_direction)
                == np.sign(fleet_index_change)
            )

        summary_rows.append(
            {
                "component": component,
                "method": method,
                "valid_pair_count": len(valid),
                "before_mean":
                    valid[before_column].mean(),
                "after_mean":
                    valid[after_column].mean(),
                "mean_index_change":
                    fleet_index_change,
                "before_min":
                    valid[before_column].min(),
                "before_max":
                    valid[before_column].max(),
                "after_min":
                    valid[after_column].min(),
                "after_max":
                    valid[after_column].max(),
                "masked_change_count":
                    int(masked_change.sum()),
                "direction_conflict_count":
                    int(direction_conflict.sum()),
                "fleet_metric_direction":
                    fleet_metric_direction,
                "fleet_direction_match":
                    fleet_direction_match,
            }
        )

summary = pd.DataFrame(summary_rows)

DETAIL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

SUMMARY_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

detail.to_csv(DETAIL_PATH, index=False)
summary.to_csv(SUMMARY_PATH, index=False)

print("Component index comparison saved")
print(f"Detail: {DETAIL_PATH}")
print(f"Summary: {SUMMARY_PATH}")

print("\nMethod comparison")
print(
    summary[
        [
            "component",
            "method",
            "valid_pair_count",
            "before_mean",
            "after_mean",
            "mean_index_change",
            "masked_change_count",
            "direction_conflict_count",
            "fleet_direction_match",
        ]
    ].to_string(index=False)
)