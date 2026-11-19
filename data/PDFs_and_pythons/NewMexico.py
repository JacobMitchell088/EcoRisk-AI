
import fitz
import pandas as pd
import re

pdf_path = "NewMexico.pdf"

pdf = fitz.open(pdf_path)

# The species summary is on PDF pages 4–6.
text = "\n".join(pdf[i].get_text() for i in range(3, 6))

species = []
status = None

for line in text.splitlines():
    line = line.strip()

    # Update the current listing status
    if re.match(r"^Endangered\s*\(", line):
        status = "Endangered"
        continue

    if re.match(r"^Threatened\s*\(", line):
        status = "Threatened"
        continue

    # Ignore headings and other lines
    if status is None:
        continue

    # Most entries separate the common and scientific names
    # with a comma. A few entries omit that comma.
    if "," in line:
        common_name, scientific_name = line.split(",", 1)
        scientific_name = scientific_name.strip().rstrip(",")
    else:
        # Handle entries such as:
        # gray-checkered whiptail Aspidoscelis dixoni
        # spikedace Meda fulgia
        match = re.match(
            r"^(.*?)\s+([A-Z][a-zA-Z-]+)\s+"
            r"([a-z][a-zA-Z-]+(?:\s+[a-z][a-zA-Z-]+)?)$",
            line
        )

        if not match:
            continue

        common_name = match.group(1)
        scientific_name = (
            match.group(2) + " " + match.group(3)
        )

    common_name = common_name.strip()
    scientific_name = scientific_name.strip()

    # Ignore headings or invalid rows
    if not common_name or not scientific_name:
        continue

    # Remove parentheses around subspecies descriptors
    common_name = common_name.replace("(", "").replace(")", "")

    # Remove quotation marks and commas from common names
    common_name = common_name.replace(",", "")
    common_name = common_name.replace('"', "")
    common_name = common_name.replace("'", "").strip()

    species.append({
        "Common Name": common_name,
        "Scientific Name": scientific_name,
        "Status": status,
        "Original Status": status,
        "State": "New Mexico"
    })

df = pd.DataFrame(species)

df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Status"]
)

df.to_csv("new_mexico_species.csv", index=False)

print(df.head(10))
print("\nSpecies collected:", len(df))
print("Saved to new_mexico_species.csv")