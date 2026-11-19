import fitz
import pandas as pd
import re

PDF_FILE = "kansasOff.pdf"
OUTPUT_FILE = "kansas_species.csv"

doc = fitz.open(PDF_FILE)

rows = []
status = None

for page in doc:
    lines = page.get_text("text").splitlines()

    for line in lines:
        line = line.strip()

        # Identify status sections
        if "designated endangered" in line.lower():
            status = "Endangered"
            continue

        if "designated threatened" in line.lower():
            status = "Threatened"
            continue

        # Match species lines
        match = re.match(
            r"^(.+?),\s+(.+?)\s+\([^)]*\)$",
            line
        )

        if match and status:
            common_name = match.group(1).strip()
            scientific_name = match.group(2).strip()

            rows.append({
                "Common Name": common_name,
                "Scientific Name": scientific_name,
                "Status": status,
                "Original Status": status,
                "State": "Kansas"
            })

df = pd.DataFrame(rows)

# Remove duplicate species
df = df.drop_duplicates()

df.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} species to {OUTPUT_FILE}")