from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from mygeotab import API


MAPPING_PATH = Path("data/private/vehicle_id_mapping.csv")
DEVICE_LIST_PATH = Path("data/raw/device_list.csv")
MATCHED_DEVICE_PATH = Path("data/raw/pilot_12_matched_devices.csv")
OUTPUT_PATH = Path("data/raw/geotab_statusdata_raw_sample.csv")


load_dotenv()

username = os.getenv("GEOTAB_USERNAME")
password = os.getenv("GEOTAB_PASSWORD")
database = os.getenv("GEOTAB_DATABASE")


if not MAPPING_PATH.exists():
    raise FileNotFoundError(
        "Private vehicle mapping file was not found: "
        "data/private/vehicle_id_mapping.csv"
    )

mapping_df = pd.read_csv(MAPPING_PATH)

required_columns = {
    "original_vehicle_id",
    "public_vehicle_id",
    "vehicle_type",
}

if not required_columns.issubset(mapping_df.columns):
    raise ValueError(
        f"Mapping file must contain: {sorted(required_columns)}"
    )

if mapping_df["public_vehicle_id"].duplicated().any():
    raise ValueError("public_vehicle_id values must be unique")


print("Connecting to GeoTab")

api = API(
    username=username,
    password=password,
    database=database,
)

api.authenticate()

print("Connection successful")


device_df = pd.read_csv(DEVICE_LIST_PATH)
device_df["name"] = device_df["name"].astype(str)

matched_rows = []
missing_aliases = []

for _, mapping_row in mapping_df.iterrows():
    original_vehicle_id = str(mapping_row["original_vehicle_id"])
    public_vehicle_id = str(mapping_row["public_vehicle_id"])

    match = device_df[
        device_df["name"].str.contains(
            original_vehicle_id,
            regex=False,
            na=False,
        )
    ]

    if len(match) == 1:
        matched_rows.append(
            {
                "id": match.iloc[0]["id"],
                "public_vehicle_id": public_vehicle_id,
            }
        )
        print(f"Matched: {public_vehicle_id}")

    elif len(match) == 0:
        missing_aliases.append(public_vehicle_id)
        print(f"Missing: {public_vehicle_id}")

    else:
        raise RuntimeError(
            f"Multiple GeoTab devices matched {public_vehicle_id}"
        )


matched_devices = pd.DataFrame(matched_rows)

print(f"Target vehicles: {len(mapping_df)}")
print(f"Matched vehicles: {len(matched_devices)}")

if missing_aliases:
    raise RuntimeError(
        f"Missing vehicle aliases: {missing_aliases}"
    )


MATCHED_DEVICE_PATH.parent.mkdir(parents=True, exist_ok=True)

matched_devices.to_csv(
    MATCHED_DEVICE_PATH,
    index=False,
)

print("Private matched device list saved")


start_date = datetime.now(timezone.utc) - timedelta(days=7)
end_date = datetime.now(timezone.utc)

all_statusdata = []

for _, row in matched_devices.iterrows():
    vehicle_alias = row["public_vehicle_id"]
    device_id = row["id"]

    print(f"Extracting StatusData for {vehicle_alias}")

    records = api.get(
        "StatusData",
        search={
            "deviceSearch": {
                "id": device_id,
            },
            "fromDate": start_date.isoformat(),
            "toDate": end_date.isoformat(),
        },
        resultsLimit=5000,
    )

    temp_df = pd.DataFrame(records)

    if temp_df.empty:
        print(f"No records found for {vehicle_alias}")
        continue

    temp_df["vehicle"] = vehicle_alias
    all_statusdata.append(temp_df)

    print(f"{vehicle_alias}: {len(temp_df)} records")


if all_statusdata:
    statusdata_df = pd.concat(
        all_statusdata,
        ignore_index=True,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    statusdata_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Raw StatusData saved")
    print(f"Total rows: {len(statusdata_df)}")

else:
    print("No StatusData extracted")