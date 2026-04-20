import pathlib
import requests
import pandas as pd


url = "https://naturalheritage.illinois.gov/content/soi/naturalheritage/en/dataresearch/access-our-data/species-by-county/jcr:content/responsivegrid/container/container_293684588/container/data_table.datatablejson.json"


#make myself seem real for getting data
headers = {
    "User-Agent": "Mozilla/5.0"
}


#grab data
response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()


#format similar to what reg tables are like
columns = [
    "County",
    "Scientific Name",
    "Common Name",
    "Status",
    "Category",
    "Date",
    "Count"
]

df = pd.DataFrame(data["data"], columns=columns)    #convert

output_path = pathlib.Path(__file__).parent.parent / "data" / "IsEndangered.csv"
df.to_csv(output_path, index=False, encoding="utf-8")  #save

print(f"Saved to {output_path}")
