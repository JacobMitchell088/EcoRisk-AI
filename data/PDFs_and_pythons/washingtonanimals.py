
import fitz
import pandas as pd
from collections import defaultdict

# Open the local PDF file
pdf = fitz.open("Washington_Animals.pdf")

species = []

for page in pdf:
    # Group words that appear on the same horizontal line
    lines = defaultdict(list)

    for word in page.get_text("words"):
        x0, y0, x1, y1, text = word[:5]
        lines[round(y0, 1)].append((x0, text))

    for y in sorted(lines):
        words = sorted(lines[y], key=lambda item: item[0])

        # Extract text from the PDF's column positions
        common_name = " ".join(
            text for x, text in words if 20 <= x < 210
        ).strip()

        scientific_name = " ".join(
            text for x, text in words if 220 <= x < 400
        ).strip()

        original_status = " ".join(
            text for x, text in words if 580 <= x < 645
        ).strip()

        # Keep only endangered and threatened entries
        if original_status not in ["E", "T", "E-Part", "T-Part"]:
            continue

        if original_status in ["E", "E-Part"]:
            status = "Endangered"
        else:
            status = "Threatened"

        # Skip incomplete rows
        if not common_name or not scientific_name:
            continue

        species.append({
            "Common Name": common_name,
            "Scientific Name": scientific_name,
            "Status": status,
            "Original Status": original_status,
            "State": "Washington"
        })

pdf.close()

# Create the DataFrame
df = pd.DataFrame(species)

columns = [
    "Common Name",
    "Scientific Name",
    "Status",
    "Original Status",
    "State"
]

df = df[columns]
df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Original Status"]
)

# Save the CSV
df.to_csv("washington_animals.csv", index=False)

print(df.to_string(index=False))
print("\nTotal species:", len(df))
print("\nCounts by status:")
print(df["Status"].value_counts())
print("\nSaved to washington_animals.csv")

