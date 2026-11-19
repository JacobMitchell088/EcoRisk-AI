
import pdfplumber
import pandas as pd
import re
from pathlib import Path

# PDF files
PDF_FILES = {
    "animals": {
        "file": "Montana_animals.pdf",
        "state_rank_column": 3
    },
    "plants": {
        "file": "Montana_Plants.pdf",
        "state_rank_column": 4
    }
}

OUTPUT = "montana_threatened_endangered.csv"


def clean(value):
    """Remove extra spaces and line breaks."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def get_status(state_rank):
    """Apply the requested Montana classification rule."""
    state_rank = clean(state_rank).upper()

    if re.match(r"^S1(?:$|S|[A-Z?])", state_rank):
        return "Endangered"

    if re.match(r"^S2(?:$|S|[A-Z?])", state_rank):
        return "Threatened"

    return None


def scrape_pdf(pdf_file, category, rank_column):
    records = []

    if not Path(pdf_file).exists():
        print(f"File not found: {pdf_file}")
        return records

    with pdfplumber.open(pdf_file) as pdf:

        print(f"\nReading {pdf_file}...")
        print(f"Total pages: {len(pdf.pages)}")

        for page_number, page in enumerate(pdf.pages, start=1):

            tables = page.extract_tables()

            for table in tables:

                for row in table:

                    if not row or len(row) <= rank_column:
                        continue

                    # First column contains scientific and common names
                    name_cell = clean(row[0])

                    # State rank is in a different column for each PDF
                    state_rank = clean(row[rank_column])

                    # Determine whether the species qualifies
                    status = get_status(state_rank)

                    if not status or not name_cell:
                        continue

                    # Separate scientific and common names
                    name_lines = [
                        clean(line)
                        for line in str(row[0]).split("\n")
                        if clean(line)
                    ]

                    if not name_lines:
                        continue

                    scientific_name = name_lines[0]

                    # Skip anything that isn't a scientific species name
                    if not re.match(
                        r"^[A-Z][a-z-]+(?:\s+[a-z][a-z-]+)+",
                        scientific_name
                    ):
                        continue

                    common_name = (
                        name_lines[1] if len(name_lines) > 1 else ""
                    )

                    records.append({
                        "name": common_name,
                        "scientific_name": scientific_name,
                        "status": status,
                        "state": "Montana",
                        "state_rank": state_rank,
                        "category": category
                    })

    return records


# Scrape both PDFs
all_records = []

for category, settings in PDF_FILES.items():

    records = scrape_pdf(
        settings["file"],
        category,
        settings["state_rank_column"]
    )

    print(f"{category.capitalize()} records found: {len(records)}")

    all_records.extend(records)


# Create DataFrame
df = pd.DataFrame(all_records)

if not df.empty:

    # Remove duplicate species
    df = df.drop_duplicates(
        subset=["scientific_name", "category"],
        keep="first"
    )

    # Sort alphabetically
    df = df.sort_values(
        by=["category", "scientific_name"]
    )

    # Save CSV
    df.to_csv(OUTPUT, index=False)

    print("\nScraping complete!")
    print(f"Total species: {len(df)}")
    print(f"Endangered: {len(df[df['status'] == 'Endangered'])}")
    print(f"Threatened: {len(df[df['status'] == 'Threatened'])}")
    print(f"Saved to: {OUTPUT}")

else:
    print("No qualifying species were found.")
