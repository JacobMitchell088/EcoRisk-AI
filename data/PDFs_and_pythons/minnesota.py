
import fitz
import pandas as pd
import re

# Open the downloaded PDF
pdf = fitz.open("Minesotta.pdf")

species = []

# The alphabetical index is on PDF pages 11-18
for page_num in range(10, 18):
    page = pdf[page_num]

    for line in page.get_text().splitlines():

        # Extract scientific name, common name, status, and group
        match = re.match(
            r'^\s*(.+?)\s*\.{2,}\s*(.+?)\s*\.{2,}'
            r'\s*(E|T|SC)\s*\.{2,}\s*(.*?)\s*$',
            line
        )

        if match:
            scientific_name, common_name, original_status, group = (
                match.groups()
            )

            # Keep only endangered and threatened species
            if original_status in ["E", "T"]:
                if original_status == "E":
                    status = "Endangered"
                else:
                    status = "Threatened"

                species.append({
                    "Common Name": common_name.strip(),
                    "Scientific Name": scientific_name.strip(),
                    "Status": status,
                    "Original Status": original_status,
                    "State": "Minnesota"
                })

# Create the CSV
df = pd.DataFrame(species)

df = df.drop_duplicates(
    subset=["Scientific Name", "Original Status"]
)

df.to_csv("minnesota_species.csv", index=False)

print("Total species:", len(df))
print(df.head())
print("Saved to minnesota_species.csv")

pdf.close()