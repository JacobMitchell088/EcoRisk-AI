import requests
import pandas as pd


url = "https://naturalheritage.illinois.gov/content/soi/naturalheritage/en/dataresearch/access-our-data/species-by-county/jcr:content/responsivegrid/container/container_293684588/container/data_table.datatablejson.json"


#make myself seem real for getting data
headers = {
    "User-Agent": "Mozilla/5.0"
}


#graab data
response = requests.get(url, headers=headers)
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

df.to_csv("illinois_unfiltered_species.csv", index=False)  #save

print("Saved to illinois_species.csv")