
import requests
import pandas as pd
from io import StringIO

url = "https://gfp.sd.gov/threatened-endangered/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

# Read every HTML table on the page
tables = pd.read_html(StringIO(response.text))

species_tables = []

for table in tables:
    # Normalize column names
    table.columns = [
        str(col).strip().replace("\xa0", " ")
        for col in table.columns
    ]

    # Keep only tables containing the species-list columns
    required = {
        "Name",
        "Scientific Name",
        "Federal Status",
        "State Status"
    }

    if required.issubset(set(table.columns)):
        df = table[list(required)].copy()

        # Preserve the desired column order
        df = df[
            ["Name", "Scientific Name",
             "Federal Status", "State Status"]
        ]

        # Clean whitespace and empty cells
        for col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace("\xa0", " ", regex=False)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

        df = df.replace("", pd.NA).dropna(
            subset=["Name", "Scientific Name"]
        )

        species_tables.append(df)

if not species_tables:
    print("No matching species tables found.")
    print("Tables detected:", len(tables))
    for i, table in enumerate(tables):
        print(i, list(table.columns))
else:
    species = pd.concat(
        species_tables, ignore_index=True
    )

    # Remove duplicate species rows
    species = species.drop_duplicates(
        subset=["Name", "Scientific Name",
                "Federal Status", "State Status"]
    )

    species = species.fillna("")

    # Export
    # Save species list to CSV
    output_file = (
        r"C:\Users\mwold\OneDrive\Documents\finalProjectTestGrounds"
        r"\south_dakota_threatened_endangered.csv"
    )

    species.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
    )

print(f"Saved {len(species)} species rows to:")
print(output_file)

print("Species rows:", len(species))
print(species.to_string(index=False))
print("Saved CSV and Excel files.")
