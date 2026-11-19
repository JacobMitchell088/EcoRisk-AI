import pandas as pd

url = (
    "https://www.dfw.state.or.us/wildlife/diversity/species/"
    "threatened_endangered_candidate_list.asp"
)

# Read tables without assuming pandas can detect the headers
tables = pd.read_html(url, header=None)

df = None

# Find the table containing the actual species column headers
for table_num, table in enumerate(tables):
    for row_idx in range(len(table)):
        row_values = [
            str(value).strip().lower()
            for value in table.iloc[row_idx].tolist()
        ]

        if (
            "common name" in row_values
            and "scientific name" in row_values
        ):
            df = table.iloc[row_idx + 1:].copy()
            df.columns = [
                str(value).strip().replace("*", "")
                for value in table.iloc[row_idx].tolist()
            ]

            print(f"Found species table: {table_num}")
            print("Columns:", df.columns.tolist())
            break

    if df is not None:
        break

if df is None:
    raise ValueError(
        "Could not find the species table. "
        "Print the first few rows of each table to inspect the website."
    )

# Standardize column names
df.columns = [str(col).strip() for col in df.columns]

df = df.rename(columns={
    "Common Name": "Name",
    "Scientific Name": "Scientific Name",
    "State Status": "Status"
})

# Verify that the required columns exist
required = ["Name", "Scientific Name", "Status"]
missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(
        f"Missing columns: {missing}. "
        f"Columns found: {df.columns.tolist()}"
    )

# Clean the data
for col in required:
    df[col] = df[col].fillna("").astype(str).str.strip()

df["Status"] = df["Status"].str.upper()

# Keep only species with an Oregon state listing:
# E = Endangered, T = Threatened
df = df[df["Status"].str.startswith(("E", "T"))].copy()

# Convert status codes into readable labels
df["Status"] = df["Status"].str[0].map({
    "E": "Endangered",
    "T": "Threatened"
})

# Add state and remove incomplete/duplicate records
df["State"] = "Oregon"

df = df[
    df["Name"].ne("")
    & df["Scientific Name"].ne("")
].drop_duplicates(
    subset=["Name", "Scientific Name", "Status", "State"]
)

# Arrange and save the requested columns
df = df[["Name", "Scientific Name", "Status", "State"]]
df = df.sort_values("Name").reset_index(drop=True)

df.to_csv("oregon_threatened_endangered.csv", index=False)

print("\nFinal dataset:")
print(df.to_string(index=False))
print(f"\nTotal records: {len(df)}")
print("Saved as oregon_threatened_endangered.csv")