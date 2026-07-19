import pandas as pd
import ast

df = pd.read_csv("data/raw/geotab_statusdata_raw_full.csv")

def get_diagnostic_name(x):
    try:
        value = ast.literal_eval(x)
        return value.get("id", None)
    except:
        return None

df["diagnostic_id"] = df["diagnostic"].apply(get_diagnostic_name)

print("\nUnique diagnostic count")
print(df["diagnostic_id"].nunique())

print("\nTop diagnostics")
print(df["diagnostic_id"].value_counts().head(30))

df[["vehicle", "dateTime", "diagnostic_id", "data"]].to_csv(
    "data/raw/geotab_statusdata_diagnostic_preview.csv",
    index=False
)

print("\nDiagnostic preview saved")