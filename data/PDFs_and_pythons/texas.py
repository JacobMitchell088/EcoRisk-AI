
import re
import pdfplumber
import pandas as pd
from pathlib import Path

# PDF is in the same folder as this script
PDF = Path(__file__).parent / "Texas.pdf"
OUTPUT = Path(__file__).parent / "texas_threatened_endangered.csv"


def clean(value):
    return " ".join(value.replace("\xa0", " ").split()).strip()


def parse_species(line):
    line = clean(line)

    # Standard format: Common Name (Scientific name)
    if "(" in line:
        common, scientific = line.split("(", 1)
        common = clean(common)
        scientific = clean(scientific).rstrip(")").strip()

        if common and scientific:
            return common, scientific

    # Handle entries where the PDF omits parentheses.
    # Examples:
    # Tropical Parula Setophaga pitiayumi
    # Speckled Racer Drymobius margaritiferus)
    match = re.match(
        r"^(.+?)\s+([A-Z][a-z]+(?:\s+[a-z][a-z.-]*)+)\)?$",
        line
    )

    if match:
        return clean(match.group(1)), clean(match.group(2))

    return None, None


def main():
    if not Path(PDF).exists():
        print(f"PDF not found: {PDF}")
        return

    records = []
    current_status = None

    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            for line in text.splitlines():
                line = clean(line)
                lower = line.lower()

                # Identify status sections in document order.
                if "texas endangered plants" in lower:
                    current_status = "State Endangered"
                    continue

                if "texas threatened plants" in lower:
                    current_status = "State Threatened"
                    continue

                if "state-listed threatened species in texas" in lower:
                    current_status = "State Threatened"
                    continue

                if lower == "endangered species":
                    current_status = "State Endangered"
                    continue

                # Ignore headings, category labels, and empty lines.
                if not line or current_status is None:
                    continue

                if lower.startswith("figure:"):
                    continue

                if lower in {
                    "mammals",
                    "birds",
                    "reptiles",
                    "amphibians",
                    "fishes",
                    "aquatic invertebrates",
                }:
                    continue

                common, scientific = parse_species(line)

                if not common or not scientific:
                    continue

                records.append({
                    "State": "Texas",
                    "Common Name": common,
                    "Scientific Name": scientific,
                    "State Status": current_status
                })

    if not records:
        print("No species extracted. Check the PDF format.")
        return

    df = pd.DataFrame(records).drop_duplicates()

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print(f"Species extracted: {len(df)}")
    print("\nCounts by status:")
    print(df["State Status"].value_counts().to_string())
    print(f"\nCSV saved to:\n{OUTPUT}")

    print("\nFirst 10 records:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
