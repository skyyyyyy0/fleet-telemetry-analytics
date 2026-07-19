import pandas as pd

df = pd.read_csv("data/raw/geotab_statusdata_raw_full.csv")

print("\nDataset Shape")
print(df.shape)

print("\nColumns")
print(df.columns.tolist())

print("\nFirst 5 Rows")
print(df.head())

print("\nMissing Values")
print(df.isnull().sum().sort_values(ascending=False).head(20))