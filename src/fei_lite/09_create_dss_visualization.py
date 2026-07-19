import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path("data/processed/dss_scores.csv")
output_path = Path("outputs/charts/dss_before_after_chart.png")

df = pd.read_csv(input_path)

df = df.dropna(subset=["before_dss", "after_dss"]).copy()

df = df.sort_values(
    "driving_risk_change_pct",
    ascending=True
)

vehicles = df["vehicle"]
before_dss = df["before_dss"]
after_dss = df["after_dss"]

x = range(len(df))
bar_width = 0.4

plt.figure(figsize=(12, 7))

plt.bar(
    [i - bar_width / 2 for i in x],
    before_dss,
    width=bar_width,
    label="Before DSS"
)

plt.bar(
    [i + bar_width / 2 for i in x],
    after_dss,
    width=bar_width,
    label="After DSS"
)

plt.axhline(
    y=100,
    linestyle="--",
    linewidth=1,
    label="Baseline DSS = 100"
)

plt.xticks(
    x,
    vehicles,
    rotation=75,
    ha="right"
)

plt.ylabel("Driving Smoothness Score (DSS)")
plt.title("Before vs After Driving Smoothness Score by Vehicle")

plt.legend()
plt.tight_layout()

output_path.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(output_path, dpi=300)
plt.close()

print("DSS chart saved")
print(f"Output: {output_path}")