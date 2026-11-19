




from bs4 import BeautifulSoup
import pandas as pd
import re

filename = "NewJerseySite.htm"

with open(filename, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file.read(), "html.parser")

results = []


def clean(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\*+", "", text)
    text = " ".join(text.split()).strip()

    # Remove trailing population markers
    text = re.sub(r"\s+(BR|NB)$", "", text)

    # Swap common names formatted as "Name, Descriptor"
    if "," in text:
        parts = text.split(",", 1)
        text = parts[1].strip() + " " + parts[0].strip()

    return text

def add_species(common, scientific, status):
    common = clean(common)
    scientific = clean(scientific)

    if not common or not scientific:
        return

    # Skip table headings and footnotes
    if common.lower() in ["endangered", "threatened"]:
        return

    # Scientific names should begin with a capitalized genus
    if not re.match(r"^[A-Z][a-z-]+(?:\s+[a-z][a-z.-]+)+$", scientific):
        return

    results.append({
        "Common Name": common,
        "Scientific Name": scientific,
        "Status": status,
        "Original Status": status,
        "State": "New Jersey"
    })

for table in soup.find_all("table"):
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"], recursive=False)

        # Print and inspect the cell layout if needed
        values = [clean(cell.get_text(" ", strip=True)) for cell in cells]

        if len(values) < 4:
            continue

        # Two-column species lists:
        # Endangered common | Endangered scientific |
        # Threatened common | Threatened scientific
        if len(values) == 4:
            add_species(values[0], values[1], "Endangered")
            add_species(values[2], values[3], "Threatened")

        elif len(values) >= 5:
            add_species(values[0], values[1], "Endangered")
            add_species(values[3], values[4], "Threatened")

df = pd.DataFrame(results, columns=[
    "Common Name",
    "Scientific Name",
    "Status",
    "Original Status",
    "State"
]).drop_duplicates()

df.to_csv("new_jersey_species.csv", index=False)

print("Species found:", len(df))
print("Saved to new_jersey_species.csv")