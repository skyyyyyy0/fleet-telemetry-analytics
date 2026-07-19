from mygeotab import API
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

username = os.getenv("GEOTAB_USERNAME")
password = os.getenv("GEOTAB_PASSWORD")
database = os.getenv("GEOTAB_DATABASE")

print("Connecting to GeoTab")

api = API(
    username=username,
    password=password,
    database=database
)

api.authenticate()

print("Connection successful")

devices = api.get("Device")

device_df = pd.DataFrame(devices)

print(f"Total devices found: {len(device_df)}")

device_df.to_csv(
    "data/raw/device_list.csv",
    index=False
)

print("Device list saved")