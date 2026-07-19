import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path(
    "outputs/tables/coolant_temperature_summary.csv"
)

output_path = Path(
    "outputs/charts/coolant_temperature_chart.png"
)

df = pd.read_csv(input_path)

df = df.sort_values(
    "temp_change",
    ascending=False
)

vehicles = df["vehicle"]

before_temp = df["before_avg_coolant_temp"]
after_temp = df["after_avg_coolant_temp"]

x = range(len(df))
bar_width = 0.4

plt.figure(figsize=(12, 7))

plt.bar(
    [i - bar_width / 2 for i in x],
    before_temp,
    width=bar_width,
    label="Before"
)

plt.bar(
    [i + bar_width / 2 for i in x],
    after_temp,
    width=bar_width,
    label="After"
)

plt.xticks(
    x,
    vehicles,
    rotation=75,
    ha="right"
)

plt.ylabel("Average Coolant Temperature (°C)")
plt.title("Before vs After Average Coolant Temperature")

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

print("Coolant temperature chart saved")
print(f"Output: {output_path}")