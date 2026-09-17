import pandas as pd

def find_status_column(df):
    possible_names = [
        "state status",
        "ststat",
        "state_status",
        "state-status",
        "state listing status",
        "state protection status",
        "status"
    ]

    for column in df.columns:
        column_lower = column.lower().strip()

        for name in possible_names:
            if name in column_lower:
                return column

    raise ValueError("Could not find a state status column")


def normalize_status(status):
    if pd.isna(status):
        return None

    status = str(status).strip().upper()

    endangered_labels = {
        "E",
        "LE",
        "SE",
        "ENDANGERED",
        "STATE ENDANGERED",
        "LISTED ENDANGERED"
    }

    threatened_labels = {
        "T",
        "LT",
        "ST",
        "THREATENED",
        "STATE THREATENED",
        "LISTED THREATENED"
    }

    if status in endangered_labels:
        return "Endangered"

    elif status in threatened_labels:
        return "Threatened"

    return None


def convert_species_csv(
    input_file,
    #output_file,
    common_name_column,
    scientific_name_column,
    status_column,
    state
):
    # Read CSV
    df = pd.read_csv(input_file)

    print(f"\nProcessing: {input_file}")       

    print(f"Using status column: {status_column}")

    df["Original Status"] = df[status_column]

    # Normalize status
    df["Status"] = df["Original Status"].apply(normalize_status)

    # Only keep Endangered and Threatened
    df = df[df["Status"].notna()].copy()

    # Create standardized dataframe
    output_df = pd.DataFrame({
        "Common Name": df[common_name_column],
        "Scientific Name": df[scientific_name_column],
        "Status": df[status_column],
        #"Original Status": df["Original Status"],
        "State": state
    })

    # Save individual standardized CSV
    #output_df.to_csv(output_file, index=False)

    #print(f"Saved: {output_file}")
    print(f"Records: {len(output_df)}")

    # Return dataframe so main.py can combine it
    return output_df