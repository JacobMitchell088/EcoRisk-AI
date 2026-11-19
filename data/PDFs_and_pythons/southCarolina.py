
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
import re

# Input and output files
HTML_FILE = "southCarolinaEndangered.htm"
OUTPUT = "south_carolina_endangered_animals.csv"

# Locate the HTML file in the same folder as this script
BASE_DIR = Path(__file__).parent
html_path = BASE_DIR / HTML_FILE

if not html_path.exists():
    raise FileNotFoundError(f"Could not find {HTML_FILE}")

# Read saved webpage
with open(html_path, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Find the regulation's species list
main_section = soup.find("div", class_="statereg-text")

if main_section is None:
    raise ValueError("Could not find the species list in the HTML file.")

# The first numbered section contains the endangered wildlife list
sections = main_section.find_all(
    "div",
    class_="subsect",
    recursive=False
)

if not sections:
    raise ValueError("Could not find the numbered species section.")

species_section = sections[0]

records = []

# Find animal categories: Birds, Fish, Mammals, etc.
categories = species_section.find_all(
    "div",
    class_=lambda c: c and "indent1" in c.split(),
    recursive=False
)

for category_group in categories:

    # Extract category name from its direct text
    category = " ".join(
        category_group.find_all(string=True, recursive=False)
    ).strip()

    # Remove extra whitespace
    category = re.sub(r"\s+", " ", category)

    # Find individual species under this category
    species_items = category_group.find_all(
        "div",
        class_=lambda c: c and "indent2" in c.split(),
        recursive=False
    )

    for item in species_items:

        species_text = item.get_text(" ", strip=True)

        # Remove list numbering (1., 2., 3., etc.)
        species_text = re.sub(
            r"^\d+\.\s*",
            "",
            species_text
        )

        # Separate common name and scientific name
        match = re.match(
            r"^(.*?)\s*\(([^()]*)\)\s*$",
            species_text
        )

        if not match:
            print("Could not parse:", species_text)
            continue

        common_name = match.group(1).strip()
        scientific_name = match.group(2).strip()

        records.append({
            "name": common_name,
            "scientific_name": scientific_name,
            "status": "Endangered",
            "state": "South Carolina",
            "category": category
        })

# Create DataFrame
df = pd.DataFrame(records)

if not df.empty:

    # Remove duplicate species
    df = df.drop_duplicates(
        subset=["scientific_name"],
        keep="first"
    )

    # Sort alphabetically
    df = df.sort_values("name")

    # Save CSV
    output_path = BASE_DIR / OUTPUT
    df.to_csv(output_path, index=False)

    print("\nScraping complete!")
    print("Total species:", len(df))
    print("\nSpecies by category:")
    print(df["category"].value_counts().to_string())
    print("\nSaved to:", output_path)

else:
    print("No species were extracted.")
