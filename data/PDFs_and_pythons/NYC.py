
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup

url = "https://dec.ny.gov/nature/animals-fish-plants/biodiversity-species-conservation/endangered-species/list"

response = requests.get(url, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

all_species = []
statuses = ["Endangered", "Threatened"]

for status in statuses:

    # Find the heading for this status
    heading = soup.find(
        lambda tag: tag.name in ["h2", "h3", "h4"]
        and tag.get_text(" ", strip=True) == status
    )

    if heading is None:
        print(f"Could not find heading: {status}")
        continue

    # Find the table following the heading
    table = heading.find_next("table")

    if table is None:
        print(f"Could not find table for: {status}")
        continue

    count = 0

    for row in table.find_all("tr"):

        cells = row.find_all("td")

        # Skip headers and rows without both names.
        # Using the last two cells handles rows with rowspan.
        if len(cells) < 2:
            continue

        common_cell = cells[-2]
        scientific_cell = cells[-1]

        # Remove footnote markers
        for sup in common_cell.find_all("sup"):
            sup.decompose()

        common_name = common_cell.get_text(" ", strip=True)
        scientific_name = scientific_cell.get_text(" ", strip=True)

        # Remove any remaining leading footnote numbers
        common_name = re.sub(
            r"^[\d¹²³⁴⁵⁶⁷⁸⁹⁰]+(?:\s*,\s*[\d¹²³⁴⁵⁶⁷⁸⁹⁰]+)*\s*",
            "",
            common_name
        )

        # Convert names like "Kestrel, American" to "American Kestrel"
        if common_name.count(",") == 1:
            parts = [part.strip() for part in common_name.split(",")]
            if all(parts):
                common_name = parts[1] + " " + parts[0]

        # Remove commas and quotation marks
        common_name = common_name.replace(",", "")
        common_name = common_name.replace('"', "")
        common_name = common_name.replace("'", "").strip()

        if not common_name or not scientific_name:
            continue

        if common_name.lower() == "none listed":
            continue

        all_species.append({
            "Common Name": common_name,
            "Scientific Name": scientific_name,
            "Status": status,
            "Original Status": status,
            "State": "New York"
        })

        count += 1

    print(f"{status}: collected {count} species")

# Remove duplicates
df = pd.DataFrame(all_species)
df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Status"]
)

df.to_csv("new_york_species.csv", index=False)

print(f"\nTotal species collected: {len(df)}")
print("Saved to new_york_species.csv")
print(df.head(10))