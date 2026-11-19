
import pdfplumber
import pandas as pd
import re
from pathlib import Path

PDF = "Alabama.pdf"
OUTPUT = "alabama_threatened_animals.csv"

BASE_DIR = Path(__file__).parent
pdf_path = BASE_DIR / PDF
output_path = BASE_DIR / OUTPUT

if not pdf_path.exists():
    raise FileNotFoundError(f"Could not find {PDF}")

records = []

# Physical PDF page number and table index -> animal category
categories = {
    (1, 0): "Fish",
    (2, 0): "Fish",
    (2, 1): "Amphibians",
    (2, 2): "Reptiles",
    (3, 0): "Reptiles",
    (3, 1): "Mammals"
}

with pdfplumber.open(pdf_path) as pdf:

    # Named animal tables are on pages 1 through 3
    for page_index, page in enumerate(pdf.pages[:3]):
        page_number = page_index + 1
        tables = page.extract_tables()

        for table_index, table in enumerate(tables):
            category = categories.get(
                (page_number, table_index),
                "Unknown"
            )

            for row in table:

                if not row or len(row) < 2:
                    continue

                common_name = row[0]
                scientific_name = row[1]

                if not common_name or not scientific_name:
                    continue

                common_name = re.sub(r"^[•\s]+", "", common_name).strip()

                if "," in common_name:
                    parts = common_name.split(",", 1)
                    common_name = parts[1].strip() + " " + parts[0].strip()

                scientific_name = scientific_name.strip()

                # Skip table headings
                if common_name.lower() == "common name":
                    continue

                if scientific_name.lower() == "scientific name":
                    continue

                records.append({
                    "name": common_name,
                    "scientific_name": scientific_name,
                    "status": "Threatened",
                    "state": "Alabama",
                    "category": category
                })

df = pd.DataFrame(records)

if not df.empty:
    df = df.drop_duplicates(
        subset=["name", "scientific_name"]
    )

    df = df.sort_values("name")

    df.to_csv(output_path, index=False)

    print("Scraping complete!")
    print("Total animal entries:", len(df))

    print("\nAnimals by category:")
    print(df["category"].value_counts().to_string())

    print("\nSaved to:", output_path)

else:
    print("No animals were extracted.")
