

import fitz
import pandas as pd
import re

pdf = fitz.open("Ohio.pdf")

species = []

# PDF pages 4–5 contain endangered species.
# PDF page 6 contains threatened species.
pages = {
    3: "Endangered",
    4: "Endangered",
    5: "Threatened"
}

scientific_pattern = re.compile(
    r"^[A-Z][A-Za-z-]+"
    r"(?:\s+\([^)]+\))?"
    r"(?:\s+[a-z][A-Za-z-]+)+$"
)

for page_number, status in pages.items():
    page = pdf[page_number]
    lines = []

    # Extract individual text lines with their coordinates.
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            x0, y0, x1, y1 = line["bbox"]
            text = " ".join(
                span["text"].strip()
                for span in line["spans"]
                if span["text"].strip()
            ).strip()

            if text:
                lines.append({
                    "x": x0,
                    "y": (y0 + y1) / 2,
                    "text": text
                })

    # Find scientific names in each of the two columns.
    for sci_line in lines:
        x = sci_line["x"]
        scientific_name = sci_line["text"]

        # Scientific-name columns are around x=179 and x=464.
        if not (170 <= x <= 305 or 455 <= x <= 600):
            continue

        if not scientific_pattern.fullmatch(scientific_name):
            continue

        # Find which common-name column belongs to this name.
        if x < 305:
            common_min, common_max = 30, 175
        else:
            common_min, common_max = 305, 455

        # Gather common-name text close to the scientific name.
        # This allows names that wrap onto a second line.
        nearby = [
            line for line in lines
            if common_min <= line["x"] <= common_max
            and abs(line["y"] - sci_line["y"]) <= 8
        ]

        common_name = " ".join(
            item["text"] for item in sorted(
                nearby, key=lambda item: item["y"]
            )
        )

        # Remove federal listing markers and clean punctuation.
        common_name = re.sub(r"\s+\*[ET]\b", "", common_name)
        common_name = common_name.replace("*E", "").replace("*T", "")
        common_name = common_name.replace(",", "").replace('"', "")
        common_name = re.sub(r"\s+", " ", common_name).strip()

        species.append({
            "Common Name": common_name,
            "Scientific Name": scientific_name,
            "Status": status,
            "Original Status": status,
            "State": "Ohio"
        })

# Remove duplicate records.
df = pd.DataFrame(species)
df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Status"]
)

df.to_csv("ohio_species.csv", index=False, encoding="utf-8-sig")

print(f"Saved {len(df)} species to ohio_species.csv")
print(df.head(10).to_string(index=False))