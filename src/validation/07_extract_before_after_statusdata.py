from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import os

import pandas as pd
from dotenv import load_dotenv
from mygeotab import API


KST = ZoneInfo("Asia/Seoul")

MAPPING_PATH = Path("data/private/vehicle_id_mapping.csv")
DEVICE_LIST_PATH = Path("data/raw/device_list.csv")

OUTPUT_PATHS = {
    "before": Path("data/raw/before_statusdata_raw.csv"),
    "after": Path("data/raw/after_statusdata_raw.csv"),
}


def load_vehicle_mapping():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            "Private mapping file was not found: "
            "data/private/vehicle_id_mapping.csv"
        )

    mapping_df = pd.read_csv(MAPPING_PATH)

    required_columns = {
        "original_vehicle_id",
        "public_vehicle_id",
        "vehicle_type",
        "install_date",
    }

    if not required_columns.issubset(mapping_df.columns):
        raise ValueError(
            f"Mapping file must contain: {sorted(required_columns)}"
        )

    mapping_df["install_date"] = pd.to_datetime(
        mapping_df["install_date"],
        errors="raise",
    ).dt.date

    if mapping_df["public_vehicle_id"].duplicated().any():
        raise ValueError("public_vehicle_id values must be unique")

    if len(mapping_df) != 12:
        raise ValueError("The private mapping must contain exactly 12 vehicles")

    return mapping_df


def create_analysis_windows(install_date):
    installation_boundary = pd.Timestamp(
        datetime.combine(
            install_date,
            time.min,
            tzinfo=KST,
        )
    )

    return {
        "before": (
            (
                installation_boundary
                - pd.DateOffset(months=1)
            ).to_pydatetime(),
            installation_boundary.to_pydatetime(),
        ),
        "after": (
            installation_boundary.to_pydatetime(),
            (
                installation_boundary
                + pd.DateOffset(months=1)
            ).to_pydatetime(),
        ),
    }


def make_daily_windows(start_date, end_date):
    windows = []
    current = start_date

    while current < end_date:
        next_day = current + timedelta(days=1)
        windows.append(
            (
                current,
                min(next_day, end_date),
            )
        )
        current = next_day

    return windows


def match_private_devices(device_df, mapping_df):
    device_df = device_df.copy()
    device_df["name"] = device_df["name"].astype(str)

    matched_rows = []

    for _, mapping_row in mapping_df.iterrows():
        original_vehicle_id = str(
            mapping_row["original_vehicle_id"]
        )
        public_vehicle_id = str(
            mapping_row["public_vehicle_id"]
        )

        match = device_df[
            device_df["name"].str.contains(
                original_vehicle_id,
                regex=False,
                na=False,
            )
        ]

        if len(match) == 0:
            raise RuntimeError(
                f"No GeoTab device matched {public_vehicle_id}"
            )

        if len(match) > 1:
            raise RuntimeError(
                f"Multiple GeoTab devices matched {public_vehicle_id}"
            )

        matched_rows.append(
            {
                "device_id": match.iloc[0]["id"],
                "public_vehicle_id": public_vehicle_id,
                "vehicle_type": mapping_row["vehicle_type"],
                "install_date": mapping_row["install_date"],
            }
        )

        print(f"Matched: {public_vehicle_id}")

    return pd.DataFrame(matched_rows)


def extract_period(api, matched_devices, period_name):
    all_rows = []

    for _, vehicle_row in matched_devices.iterrows():
        vehicle_alias = vehicle_row["public_vehicle_id"]

        start_date, end_date = create_analysis_windows(
            vehicle_row["install_date"]
        )[period_name]

        print(
            f"{period_name.upper()} {vehicle_alias}: "
            f"{start_date.isoformat()} to "
            f"{end_date.isoformat()}"
        )

        daily_windows = make_daily_windows(
            start_date,
            end_date,
        )

        for window_start, window_end in daily_windows:
            records = api.get(
                "StatusData",
                search={
                    "deviceSearch": {
                        "id": vehicle_row["device_id"],
                    },
                    "fromDate": window_start.isoformat(),
                    "toDate": window_end.isoformat(),
                },
                resultsLimit=50000,
            )

            temp_df = pd.DataFrame(records)

            if temp_df.empty:
                continue

            temp_df["vehicle"] = vehicle_alias
            temp_df["vehicle_type"] = vehicle_row["vehicle_type"]
            temp_df["period"] = period_name
            temp_df["analysis_start_kst"] = start_date.isoformat()
            temp_df["analysis_end_kst"] = end_date.isoformat()

            all_rows.append(temp_df)

    if not all_rows:
        raise RuntimeError(
            f"No data was extracted for {period_name}"
        )

    result_df = pd.concat(
        all_rows,
        ignore_index=True,
    )

    if "id" in result_df.columns:
        result_df = result_df.drop_duplicates(
            subset=["id"]
        )

    output_path = OUTPUT_PATHS[period_name]
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Saved {len(result_df):,} {period_name} rows "
        f"to {output_path}"
    )


def main():
    load_dotenv()

    api = API(
        username=os.getenv("GEOTAB_USERNAME"),
        password=os.getenv("GEOTAB_PASSWORD"),
        database=os.getenv("GEOTAB_DATABASE"),
    )

    api.authenticate()
    print("GeoTab connection successful")

    mapping_df = load_vehicle_mapping()
    device_df = pd.read_csv(DEVICE_LIST_PATH)

    matched_devices = match_private_devices(
        device_df,
        mapping_df,
    )

    for period_name in ("before", "after"):
        extract_period(
            api,
            matched_devices,
            period_name,
        )


if __name__ == "__main__":
    main()