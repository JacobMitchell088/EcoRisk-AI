import requests
import pandas as pd
import truststore
from io import StringIO

truststore.inject_into_ssl()

url = "https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export"

params = {
    "filter": "/species@status_category = 'Listed'",
    "format": "csv"
}

response = requests.get(
    url,
    params=params
)

response.raise_for_status()

df = pd.read_csv(StringIO(response.text))

df.to_csv("fws_federal_species.csv", index=False)

print("Saved to fws_federal_species.csv")
print(f"Downloaded {len(df)} records.")