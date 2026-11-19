
import pdfplumber
import pandas as pd
from pathlib import Path

# PDF is in the same folder as this script
PDF = Path(__file__).parent / "tennessee.pdf"
OUTPUT = Path(__file__).parent / "tennessee_threatened_endangered.csv"


def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split())


def extract_table(table, status, records):
    for row in table:
        if not row or len(row) < 2:
            continue

        common = clean(row[0])
        scientific = clean(row[1])

        if not common or not scientific:
            continue

        if common.lower() in ("common name", "reserved"):
            continue
        if scientific.lower() == "scientific name":
            continue

        records.append({
            "State": "Tennessee",
            "Common Name": common,
            "Scientific Name": scientific,
            "State Status": status
        })


def main():
    records = []

    if not PDF.exists():
        print(f"Could not find PDF: {PDF}")
        return

    with pdfplumber.open(PDF) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_number = page_index + 1
            text = page.extract_text() or ""

            if page_number in (1, 2):
                # These pages contain the endangered list.
                status = "State Endangered"

                for table in page.extract_tables():
                    extract_table(table, status, records)

            elif page_number == 3:
                # Page 3 contains the end of the endangered list,
                # followed by the start of the threatened list.
                tables = page.extract_tables()

                if tables:
                    # First table: remaining endangered species.
                    extract_table(
                        tables[0],
                        "State Endangered",
                        records
                    )

                    # Remaining tables: threatened species.
                    for table in tables[1:]:
                        extract_table(
                            table,
                            "State Threatened",
                            records
                        )

            elif page_number in (4, 5):
                # These pages continue the threatened list.
                # Page 5 also starts the management list, so exclude
                # any tables appearing after that section heading.
                tables = page.extract_tables()

                for table in tables:
                    extract_table(
                        table,
                        "State Threatened",
                        records
                    )

    if not records:
        print("No species extracted. Check the PDF format.")
        return

    df = pd.DataFrame(records).drop_duplicates()

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print(f"Species extracted: {len(df)}")
    print("\nCounts by status:")
    print(df["State Status"].value_counts().to_string())
    print(f"\nCSV saved to:\n{OUTPUT}")


if __name__ == "__main__":
    main()