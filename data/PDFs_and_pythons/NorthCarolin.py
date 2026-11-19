

import fitz
import pandas as pd
import re

pdf = fitz.open("NorthCarolina.pdf")
text = "\n".join(page.get_text() for page in pdf)

# Extract the endangered section
end_start = text.find("15A NCAC 10I .0103")
threat_start = text.find("15A NCAC 10I .0104")
special_start = text.find("15A NCAC 10I .0105")

end_section = text[end_start:threat_start]
threat_section = text[threat_start:special_start]

sections = [
    (end_section, "State-listed endangered species", "Endangered"),
    (threat_section, "State listed threatened species", "Threatened")
]

species = []

pattern = re.compile(r"^\s*(.+?)\s+\(([^()]+)\)")

for section, heading, status in sections:
    # Start at the state-listed subsection
    start = section.lower().find(heading.lower())

    if start == -1:
        print("Could not find:", heading)
        continue

    section = section[start:]

    for line in section.splitlines():
        line = line.strip()
        match = pattern.match(line)

        if not match:
            continue

        common_name = match.group(1).strip()
        scientific_name = match.group(2).strip()

        # Skip category headings
        if common_name.lower().endswith(":"):
            continue

        # Remove list lettering, such as (A), (B), (a), (b)
        common_name = re.sub(
            r"^\([A-Za-z]+\)\s*", "", common_name
        )

        # Skip empty or invalid entries
        if not common_name or not scientific_name:
            continue

        common_name = common_name.replace(",", "")
        common_name = common_name.replace('"', "")
        common_name = common_name.replace("'", "").strip()

        species.append({
            "Common Name": common_name,
            "Scientific Name": scientific_name,
            "Status": status,
            "Original Status": "State " + status,
            "State": "North Carolina"
        })

df = pd.DataFrame(species)

df = df.drop_duplicates(
    subset=["Common Name", "Scientific Name", "Status"]
)

df.to_csv("north_carolina_state_species.csv", index=False)

print(df.head(10))
print("\nSpecies collected:", len(df))
print("Saved to north_carolina_state_species.csv")