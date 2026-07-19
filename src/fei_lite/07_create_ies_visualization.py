import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path("data/processed/ies_scores.csv")
output_path = Path("outputs/charts/ies_before_after_chart.png")

df = pd.read_csv(input_path)

df = df.sort_values(
    "idle_change_pct",
    ascending=True
)

vehicles = df["vehicle"]

before_ies = df["before_ies"]
after_ies = df["after_ies"]

x = range(len(df))
bar_width = 0.4

plt.figure(figsize=(12, 7))

plt.bar(
    [i - bar_width / 2 for i in x],
    before_ies,
    width=bar_width,
    label="Before IES"
)

plt.bar(
    [i + bar_width / 2 for i in x],
    after_ies,
    width=bar_width,
    label="After IES"
)

plt.axhline(
    y=100,
    linestyle="--",
    linewidth=1,
    label="Baseline IES = 100"
)

plt.xticks(
    x,
    vehicles,
    rotation=75,
    ha="right"
)

plt.ylabel("Idle Efficiency Score (IES)")
plt.title("Before vs After Idle Efficiency Score by Vehicle")

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

print("IES chart saved")
print(f"Output: {output_path}")