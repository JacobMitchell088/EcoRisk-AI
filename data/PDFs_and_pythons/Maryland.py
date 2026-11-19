
import fitz
import pandas as pd
import re
from collections import defaultdict

pdf = fitz.open("Maryland.pdf")

species = []

# The species tables begin on PDF page 8 (index 7).
# The PDF has 25 pages total.
for page_num in range(7, len(pdf)):
    page = pdf[page_num]

    # Group extracted words into lines by vertical position
    lines = defaultdict(list)

    for word in page.get_text("words"):
        x0, y0, x1, y1, text = word[:5]
        lines[round(y0, 1)].append((x0, text))

    for y, words in sorted(lines.items()):
        columns = {
            "scientific": [],
            "common": [],
            "global_rank": [],
            "state_rank": [],
            "state_status": [],
            "federal_status": []
        }

        # Separate the PDF's six columns by horizontal position
        for x, word in sorted(words):
            if x < 200:
                columns["scientific"].append(word)
            elif x < 370:
                columns["common"].append(word)
            elif x < 430:
                columns["global_rank"].append(word)
            elif x < 485:
                columns["state_rank"].append(word)
            elif x < 515:
                columns["state_status"].append(word)
            else:
                columns["federal_status"].append(word)

        scientific = " ".join(columns["scientific"]).strip()
        common = " ".join(columns["common"]).strip()
        global_rank = "".join(columns["global_rank"]).strip()
        state_rank = "".join(columns["state_rank"]).strip()
        original_status = "".join(
            columns["state_status"]
        ).strip()

        # Confirm this line resembles a species table row
        if not scientific or not common:
            continue

        if not re.match(r"^G", global_rank):
            continue

        if not re.match(r"^S", state_rank):
            continue

        # Ignore synonym/reference rows
        if scientific.startswith("["):
            continue

        if common.lower().startswith("see "):
            continue

        # Keep only state-endangered or state-threatened species.
        # E* and T* are retained as original status values.
        base_status = original_status.rstrip("*")

        if base_status == "E":
            status = "Endangered"
        elif base_status == "T":
            status = "Threatened"
        else:
            continue

        species.append({
            "Common Name": common,
            "Scientific Name": scientific,
            "Status": status,
            "Original Status": original_status,
            "State": "Maryland"
        })

# Create and clean the output
df = pd.DataFrame(species)

if not df.empty:
    df = df.drop_duplicates(
        subset=["Scientific Name", "Original Status"]
    )

    df = df[
        [
            "Common Name",
            "Scientific Name",
            "Status",
            "Original Status",
            "State"
        ]
    ]

df.to_csv("maryland_species.csv", index=False)

print("Total species:", len(df))
print(df["Status"].value_counts())
print(df.head(10))
print("Saved to maryland_species.csv")

pdf.close()