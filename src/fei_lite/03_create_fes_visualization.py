import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path("data/processed/fes_scores.csv")
output_path = Path("outputs/charts/fes_before_after_chart.png")

df = pd.read_csv(input_path)

df = df.sort_values("fuel_efficiency_change_pct", ascending=True)

vehicles = df["vehicle"]
before_fes = df["before_fes"]
after_fes = df["after_fes"]

x = range(len(df))
bar_width = 0.4

plt.figure(figsize=(12, 7))

plt.bar(
    [i - bar_width / 2 for i in x],
    before_fes,
    width=bar_width,
    label="Before FES"
)

plt.bar(
    [i + bar_width / 2 for i in x],
    after_fes,
    width=bar_width,
    label="After FES"
)

plt.axhline(
    y=100,
    linestyle="--",
    linewidth=1,
    label="Baseline FES = 100"
)

plt.xticks(x, vehicles, rotation=75, ha="right")
plt.ylabel("Fuel Efficiency Score (FES)")
plt.title("Before vs After Fuel Efficiency Score by Vehicle")
plt.legend()
plt.tight_layout()

output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=300)
plt.close()

print("FES chart saved")
print(f"Output: {output_path}")