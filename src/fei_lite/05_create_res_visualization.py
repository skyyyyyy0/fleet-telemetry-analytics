import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path("data/processed/res_scores.csv")
output_path = Path("outputs/charts/res_before_after_chart.png")

df = pd.read_csv(input_path)

df = df.sort_values(
    "rpm_efficiency_change_pct",
    ascending=True
)

vehicles = df["vehicle"]

before_res = df["before_res"]
after_res = df["after_res"]

x = range(len(df))
bar_width = 0.4

plt.figure(figsize=(12, 7))

plt.bar(
    [i - bar_width / 2 for i in x],
    before_res,
    width=bar_width,
    label="Before RES"
)

plt.bar(
    [i + bar_width / 2 for i in x],
    after_res,
    width=bar_width,
    label="After RES"
)

plt.axhline(
    y=100,
    linestyle="--",
    linewidth=1,
    label="Baseline RES = 100"
)

plt.xticks(
    x,
    vehicles,
    rotation=75,
    ha="right"
)

plt.ylabel("RPM Efficiency Score (RES)")
plt.title("Before vs After RPM Efficiency Score by Vehicle")

plt.legend()

plt.tight_layout()

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

plt.savefig(
    output_path,
    dpi=300
)

plt.close()

print("RES chart saved")
print(f"Output: {output_path}")