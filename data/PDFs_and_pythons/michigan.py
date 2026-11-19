
import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.michigan.gov/dnr/managing-resources/wildlife/wildlife-permits/threatened-endangered-species/threatened-and-endangered-species-list"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

rows = []

# Find all table rows
for tr in soup.find_all("tr"):

    cells = tr.find_all(["td", "th"])

    if len(cells) == 4:

        taxonomic_group = cells[0].get_text(strip=True)
        common_name = cells[1].get_text(strip=True)
        scientific_name = cells[2].get_text(strip=True)
        status = cells[3].get_text(strip=True)

        # Only keep Threatened and Endangered
        if status in ["Threatened", "Endangered"]:

            rows.append({
                "Common name": common_name,
                "Scientific name": scientific_name,
                "status": status,
                "state": "Michigan"
            })

# Create dataframe
df = pd.DataFrame(rows)

# Save CSV
df.to_csv("michigan_threatened_endangered.csv", index=False)

print("Saved", len(df), "species")
print(df)

