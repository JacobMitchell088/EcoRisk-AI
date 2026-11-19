import fitz
import pandas as pd
import re

# -----------------------------
# FILE SETTINGS
# -----------------------------

PDF_FILE = "ConneticutEndThreat.pdf"
OUTPUT_FILE = "connecticut_species.csv"

# -----------------------------
# READ PDF
# -----------------------------

doc = fitz.open(PDF_FILE)

lines = []

for page in doc:
    page_lines = page.get_text("text").splitlines()
    lines.extend(page_lines)


# -----------------------------
# CLEANING FUNCTIONS
# -----------------------------

def clean(text):
    """
    Removes footnote symbols and extra whitespace.
    """
    text = text.replace("\t", " ")
    text = re.sub(r"[*+^~]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_status_line(line):
    """
    Detects lines containing only E, T, or SC,
    optionally followed by a common name.
    """

    return bool(
        re.fullmatch(r"(E|T|SC)", line)
        or re.match(r"^(E|T|SC)[ \t]+.+$", line)
    )


def get_status(line):
    """
    Returns the status and any common name
    included on the same line.
    """

    match = re.match(r"^(E|T|SC)(?:[ \t]+(.*))?$", line)

    if match:
        return match.group(1), match.group(2)

    return None, None


def looks_like_scientific_name(line):
    """
    Detects a scientific name such as:

    Myotis sodalis
    Ardea alba
    Abagrotis nefascia benjamini
    """

    return bool(
        re.search(
            r"\b[A-Z][a-z-]+\s+[a-z][a-z.-]+",
            line
        )
    )


def is_genus_line(line):
    """
    Detects a genus by itself, such as:

    Melanerpes
    """

    return bool(re.fullmatch(r"[A-Z][a-z-]+", line))


def is_species_line(line):
    """
    Detects a species epithet, such as:

    erythrocephalus
    """

    return bool(re.match(r"^[a-z][a-z.-]+", line))


# -----------------------------
# PARSE SPECIES ENTRIES
# -----------------------------

records = []
unmatched = []

i = 0

while i < len(lines):

    original_line = lines[i].strip()

    if not is_status_line(original_line):
        i += 1
        continue

    status, first_common_name = get_status(original_line)

    i += 1

    block = []

    # Some status lines contain the common name
    if first_common_name:
        block.append(first_common_name)

    # Collect lines until the next status
    while i < len(lines):

        current_line = lines[i].strip()

        if is_status_line(current_line):
            break

        if current_line:
            block.append(current_line)

        i += 1

    # Ignore Special Concern species
    if status == "SC":
        continue

    # Clean every line in the block
    block = [clean(line) for line in block if clean(line)]

    # ---------------------------------
    # FIND SCIENTIFIC NAME
    # ---------------------------------

    scientific_candidates = []

    for j, line in enumerate(block):

        # Normal scientific name on one line
        if looks_like_scientific_name(line):
            scientific_candidates.append(
                (j, line)
            )

        # Scientific name split across two lines
        if j + 1 < len(block):

            if (
                is_genus_line(line)
                and is_species_line(block[j + 1])
            ):

                scientific_name = (
                    line + " " + block[j + 1]
                )

                scientific_candidates.append(
                    (j, scientific_name)
                )

    # Use the last candidate because common names
    # can sometimes resemble scientific names
    if not scientific_candidates:

        unmatched.append({
            "Status": status,
            "Text": " | ".join(block)
        })

        continue

    scientific_index, scientific_name = (
        scientific_candidates[-1]
    )

    # ---------------------------------
    # INCLUDE ADDITIONAL SCIENTIFIC PARTS
    # ---------------------------------

    scientific_parts = [scientific_name]

    next_index = scientific_index + 1

    while next_index < len(block):

        next_line = block[next_index]

        # Include taxonomic qualifiers and epithets
        if re.match(
            r"^(ssp\.|subsp\.|var\.|f\.)\s*[a-z.-]+$",
            next_line
        ):
            scientific_parts.append(next_line)
            next_index += 1
            continue

        if (
            len(scientific_parts) > 0
            and re.fullmatch(r"[a-z][a-z.-]+", next_line)
        ):
            scientific_parts.append(next_line)
            next_index += 1
            continue

        break

    scientific_name = clean(
        " ".join(scientific_parts)
    )

    # ---------------------------------
    # GET COMMON NAME
    # ---------------------------------

    common_name_parts = block[:scientific_index]

    common_name = clean(
        " ".join(common_name_parts)
    )

    # Remove leftover formatting
    common_name = re.sub(
        r"\s*\([^)]*\)",
        lambda match: match.group(0),
        common_name
    )

    # Skip invalid entries
    if not common_name or not scientific_name:
        unmatched.append({
            "Status": status,
            "Text": " | ".join(block)
        })

        continue

    # ---------------------------------
    # SAVE RECORD
    # ---------------------------------

    records.append({
        "Common Name": common_name,
        "Scientific Name": scientific_name,
        "Status": (
            "Endangered"
            if status == "E"
            else "Threatened"
        ),
        "Original Status": status,
        "State": "Connecticut"
    })


# -----------------------------
# CREATE CSV
# -----------------------------

df = pd.DataFrame(records)

# Remove duplicate records
df = df.drop_duplicates()

# Save CSV
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

# -----------------------------
# OUTPUT RESULTS
# -----------------------------

print(f"Created: {OUTPUT_FILE}")
print(f"Species captured: {len(df)}")
print(f"Unmatched entries: {len(unmatched)}")

if unmatched:

    print("\nUNMATCHED ENTRIES:")

    for entry in unmatched:
        print(
            f"{entry['Status']} | {entry['Text']}"
        )