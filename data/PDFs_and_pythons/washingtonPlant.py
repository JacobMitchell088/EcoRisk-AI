
import fitz
import pandas as pd
import re
from collections import defaultdict

pdf = fitz.open("Washington_plant.pdf")
species = []

# Matches a scientific name beginning with a capitalized genus.
scientific_pattern = re.compile(
    r"^[A-Z][a-zA-Z-]+\s+[a-z][a-zA-Z-]+"
)

for page in pdf:
    lines = defaultdict(list)

    # Group words into horizontal lines.
    for word in page.get_text("words"):
        x0, y0, x1, y1, text = word[:5]
        lines[round(y0, 1)].append((x0, text))

    # Keep the text in the first column and the state-status column.
    left_lines = []
    status_by_y = {}

    for y in sorted(lines):
        words = sorted(lines[y], key=lambda item: item[0])

        left_text = " ".join(
            text for x, text in words if 60 <= x < 190
        ).strip()

        state_status = " ".join(
            text for x, text in words if 245 <= x < 280
        ).strip()

        if left_text:
            left_lines.append((y, left_text))

        if state_status in {"Endang", "Threat", "Sens", "Extirp"}:
            status_by_y[y] = state_status

    # Find each scientific-name line.
    starts = []

    for i, (y, text) in enumerate(left_lines):
        if scientific_pattern.match(text) and y in status_by_y:
            starts.append(i)

    for j, start in enumerate(starts):
        end = starts[j + 1] if j + 1 < len(starts) else len(left_lines)
        y, scientific_line = left_lines[start]

        original_status = status_by_y[y]

        # Keep only state Endangered and Threatened species.
        if original_status not in {"Endang", "Threat"}:
            continue

        status = (
            "Endangered"
            if original_status == "Endang"
            else "Threatened"
        )

        # Collect the lines belonging to this species.
        block = [text for _, text in left_lines[start:end]]

        # The common name is usually the final non-scientific,
        # non-parenthetical line in the block.
        common_name = ""

        for text in reversed(block[1:]):
            text = text.strip()

            if (
                text
                and not text.startswith("(")
                and not text.endswith(")")
                and not scientific_pattern.match(text)
                and not re.match(r"^[a-z(]", text)
            ):
                common_name = text
                break

        # Use the first scientific-name line.
        scientific_name = scientific_line.strip()

        if common_name:
            species.append({
                "Common Name": common_name,
                "Scientific Name": scientific_name,
                "Status": status,
                "Original Status": original_status,
                "State": "Washington"
            })

pdf.close()

columns = [
    "Common Name",
    "Scientific Name",
    "Status",
    "Original Status",
    "State"
]

df = pd.DataFrame(species, columns=columns)
df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Original Status"]
)

df.to_csv("washington_plants.csv", index=False)

print(df.to_string(index=False))
print("\nTotal species:", len(df))
print("\nCounts by status:")
print(df["Status"].value_counts())
print("\nSaved to washington_plants.csv")
