
import pdfplumber
import pandas as pd
import re
from pathlib import Path

PDF = Path("Virginia_plant.pdf")
OUTPUT = "virginia_threatened_endangered_plants.csv"

# Insects included in the PDF that should be excluded
# because this project focuses on plants.


# Match numbered entries containing scientific and common names.
pattern = re.compile(
    r"^\s*\d+\.\s+"
    r"([A-Z][a-z]+\s+[a-z]+"
    r"(?:\s+(?:var\.|subsp\.|ssp\.)\s+[a-z]+)?)"
    r",\s*(.+?)\s*$"
)

species = []
status = None

if not PDF.exists():
    raise FileNotFoundError(f"Could not find PDF: {PDF.resolve()}")

with pdfplumber.open(PDF) as pdf:
    for page in pdf.pages:
        text = page.extract_text()

        if not text:
            continue

        for line in text.splitlines():

            # Identify the status section.
            if re.search(
                r"following plant and insect species are hereby declared "
                r"an endangered species",
                line,
                re.IGNORECASE,
            ):
                status = "Endangered"
                continue

            if re.search(
                r"following plant and insect species are hereby declared "
                r"a threatened species",
                line,
                re.IGNORECASE,
            ):
                status = "Threatened"
                continue

            # Ignore text outside the two listing sections.
            if status is None:
                continue

            match = pattern.match(line)

            if not match:
                continue

            scientific_name = match.group(1).strip()
            common_name = match.group(2).strip()

            
            

            species.append({
                "name": common_name,
                "scientific_name": scientific_name,
                "status": status,
                "state": "Virginia",
            })

# Create the DataFrame.
df = pd.DataFrame(
    species,
    columns=["name", "scientific_name", "status", "state"],
)

# Remove duplicate records, if any.
df = df.drop_duplicates(
    subset=["scientific_name", "status"]
)

# Save the CSV file.
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print(f"Extracted {len(df)} plant species.")
print(f"Saved to: {Path(OUTPUT).resolve()}")
print(df.to_string(index=False))
