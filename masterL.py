import pandas as pd

from NormalizeFun import convert_species_csv


all_species = []


# --------------------------------------------------
# FEDERAL
# --------------------------------------------------

federal = convert_species_csv(
    input_file="data/fws_federal_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="ESA Listing Status",

    state="All"
)

all_species.append(federal)

#---------------------------------------------------
# Michigan
# --------------------------------------------------

michigan = convert_species_csv(
    input_file="data/michigan_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common name",
    scientific_name_column="Scientific name",
    status_column="status",

    state="Michigan"
)

all_species.append(michigan)

# --------------------------------------------------
# Missouri
# --------------------------------------------------

missouri = convert_species_csv(
     input_file="data/missouri_threatened_endangered.csv",
     #output_file="output/missouri_standardized.csv",

     common_name_column="CommonName",
     scientific_name_column="SciName",
     status_column="STSTAT",

     state="Missouri"
 )

all_species.append(missouri)

#--------------------------------------------
#MISSISISP
#-------------------------------------------

mississippi = convert_species_csv(
     input_file="data/mississippi_endangered_threatened.csv",
     #output_file="output/missouri_standardized.csv",

     common_name_column="Common Name",
     scientific_name_column="Scientific Name",
     status_column="State Status",

     state="Mississippi"
 )

all_species.append(mississippi)


# --------------------------------------------------
# Illinois
# --------------------------------------------------

illinois = convert_species_csv(
    input_file="data/illinois_species.csv",
    #output_file="data/illinois_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Illinois"
)

all_species.append(illinois)

#
# Indiana
#

Indiana = convert_species_csv(
    input_file="data/indiana_insects.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Species Name",
    status_column="STATE",

    state="Indiana"
)

all_species.append(Indiana)

Indiana = convert_species_csv(
    input_file="data/indiana_plants.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Species Name",
    status_column="STATE",

    state="Indiana"
)

all_species.append(Indiana)

#
# Iowa
#

Iowa = convert_species_csv(
    input_file="data/Iowa_anim.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Iowa"
)

all_species.append(Iowa)

Iowa = convert_species_csv(
    input_file="data/Iowa_plns.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Iowa"
)

all_species.append(Iowa)

#
#   KENTUCKY
#


kentucky = convert_species_csv(
    input_file="data/kentucky.csv",
    #output_file="data/illinois_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Kentucky"
)

all_species.append(kentucky)

#
# Wisconsin
#

Wisconsin = convert_species_csv(
    input_file="data/Wisconsin.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Wisconsin"
)

all_species.append(Wisconsin)

# --------------------------------------------------
# COMBINE EVERYTHING
# --------------------------------------------------

master_list = pd.concat(all_species, ignore_index=True)

master_list.to_csv(
    "data/master_species_list.csv",
    index=False
)

print()
print("====================================")
print("MASTER LIST CREATED")
print("====================================")
print(f"Total records: {len(master_list)}")
print("Saved to: master_species_list.csv")