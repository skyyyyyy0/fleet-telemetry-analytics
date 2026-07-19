import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

input_path = Path("data/processed/vehicle_fei_scores.csv")
output_path = Path("outputs/charts/fei_lite_ranking_chart.png")

df = pd.read_csv(input_path)

df = df.sort_values(
    "after_fei_lite",
    ascending=True
)

vehicles = df["vehicle"]
after_fei = df["after_fei_lite"]

plt.figure(figsize=(12, 8))

plt.barh(
    vehicles,
    after_fei
)

plt.xlabel("After FEI-Lite Score")
plt.ylabel("Vehicle")
plt.title("FEI-Lite Vehicle Ranking")

for index, value in enumerate(after_fei):
    plt.text(
        value + 0.5,
        index,
        f"{value:.1f}",
        va="center"
    )

plt.xlim(0, 105)

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

print("FEI-Lite ranking chart saved")
print(f"Output: {output_path}")