
import pdfplumber
import pandas as pd
import re
from pathlib import Path

PDF = "rhodeIslandAnimals.pdf"
OUTPUT = "rhode_island_threatened_endangered.csv"

BASE_DIR = Path(__file__).parent
pdf_path = BASE_DIR / PDF
output_path = BASE_DIR / OUTPUT

if not pdf_path.exists():
    raise FileNotFoundError(f"Could not find {PDF}")

records = []

scientific_pattern = re.compile(
    r"^([A-Z][A-Za-z-]+(?:\s+(?:[a-z][A-Za-z.-]*|\(\*\))){1,3})\s+(.+)$"
)

status_pattern = re.compile(
    r"\s+((?:FE|FT|SE|ST|C|SH)"
    r"(?:\s*\(\d{4}\))?"
    r"(?:/(?:FE|FT|SE|ST|C|SH|P))*"
    r"(?:\s*\(\d{4}\))?"
    r"(?:/P)?)\s*$"
)

with pdfplumber.open(pdf_path) as pdf:

    for page in pdf.pages:
        text = page.extract_text()

        if not text:
            continue

        for line in text.splitlines():

            line = re.sub(r"\s+", " ", line).strip()

            status_match = status_pattern.search(line)

            if not status_match:
                continue

            original_status = status_match.group(1).strip()

            # Get individual status codes
            codes = re.findall(
                r"\b(FE|FT|SE|ST|C|SH|P)\b",
                original_status
            )

            # Keep ONLY State Endangered and State Threatened
            if "SE" not in codes and "ST" not in codes:
                continue

            species_text = line[:status_match.start()].strip()

            name_match = scientific_pattern.match(species_text)

            if not name_match:
                print("Could not parse:", line)
                continue

            scientific_name = name_match.group(1).strip()
            common_name = name_match.group(2).strip().rstrip(" .")

            # Assign state status
            if "SE" in codes:
                status = "Endangered"
            else:
                status = "Threatened"

            records.append({
                "name": common_name,
                "scientific_name": scientific_name,
                "status": status,
                "original_status": original_status,
                "state": "Rhode Island"
            })

df = pd.DataFrame(records)

if not df.empty:

    df = df.drop_duplicates(
        subset=["scientific_name", "original_status"]
    )

    df = df.sort_values("name")

    df.to_csv(output_path, index=False)

    print("\nScraping complete!")
    print("Total species:", len(df))

    print("\nSpecies by status:")
    print(df["status"].value_counts().to_string())

    print("\nSaved to:", output_path)

else:
    print("No ST or SE species were extracted.")
