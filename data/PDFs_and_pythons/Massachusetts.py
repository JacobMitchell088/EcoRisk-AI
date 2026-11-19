#Massachusetts


import pdfplumber
import pandas as pd

pdf_file = "Massechuesetts.pdf"
species = []

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()

        for table in tables:
            if not table:
                continue

            # Find the table header
            header_row = None

            for i, row in enumerate(table[:4]):
                text = " ".join(str(cell or "") for cell in row).lower()

                if (
                    "common name" in text
                    and "scientific name" in text
                    and "ma" in text
                ):
                    header_row = i
                    break

            if header_row is None:
                continue

            # Read the species rows below the header
            for row in table[header_row + 1:]:
                if len(row) < 3:
                    continue

                common_name = " ".join(
                    (row[0] or "").split()
                )
                scientific_name = " ".join(
                    (row[1] or "").split()
                )
                original_status = (row[2] or "").strip().upper()

                # Keep only Massachusetts endangered/threatened species
                if original_status == "E":
                    status = "Endangered"
                elif original_status == "T":
                    status = "Threatened"
                else:
                    continue

                if not common_name or not scientific_name:
                    continue

                species.append({
                    "Common Name": common_name,
                    "Scientific Name": scientific_name,
                    "Status": status,
                    "Original Status": original_status,
                    "State": "Massachusetts"
                })

# Remove repeated rows caused by overlapping PDF tables
df = pd.DataFrame(species)

if not df.empty:
    df = df.drop_duplicates(
        subset=[
            "Common Name",
            "Scientific Name",
            "Original Status"
        ]
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

df.to_csv("massachusetts_species.csv", index=False)

print("Total species:", len(df))
print(df["Status"].value_counts())
print(df.head(10))
print("Saved to massachusetts_species.csv")