import pandas as pd
import csv

# Read CSV
df = pd.read_csv("Pennsylvania.csv", dtype=str, keep_default_na=False)

# Clean column names
df.columns = df.columns.str.strip().str.replace('"', '')

# Clean every cell
for col in df.columns:
    df[col] = df[col].str.strip().str.strip('"')

# Remove duplicate rows
df.drop_duplicates(inplace=True)

# Save cleaned CSV
df.to_csv(
    "data/Pennsylvania_cleaned.csv",
    index=False,
    quoting=csv.QUOTE_MINIMAL
)

print("Pennsylvania.csv cleaned successfully!")