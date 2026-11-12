import pandas as pd

from normalize_func import convert_species_csv


all_species = []


# --------------------------------------------------
# FEDERAL
# --------------------------------------------------

federal = convert_species_csv(
    input_file="data/state_lists/fws_federal_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="ESA Listing Status",

    state="All"
)

all_species.append(federal)

#
# Alabama
#

Alabama = convert_species_csv(
    input_file="data/state_lists/alabama_threatened_animals.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="Alabama"
)

all_species.append(Alabama)

#
# Alaska
#

Alaska = convert_species_csv(
    input_file="data/state_lists/Alaska.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Alaska"
)

all_species.append(Alaska)

#
# Arizona
#

Arizona = convert_species_csv(
    input_file="data/state_lists/Arizona_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="SGCN",

    state="Arizona"
)

all_species.append(Arizona)

#
# Arkansas
#

Arkansas = convert_species_csv(
    input_file="data/state_lists/arkansas_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Arkansas"
)

all_species.append(Arkansas)


#
# California
#

California_1 = convert_species_csv(
    input_file="data/state_lists/california_animals.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="California"
)

all_species.append(California_1)


California_2 = convert_species_csv(
    input_file="data/state_lists/california_plants.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="California"
)

all_species.append(California_2)

#
# Colorado
#

Colorado = convert_species_csv(
    input_file="data/state_lists/ColoradoEndThreat.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="SCOMNAME",
    scientific_name_column="GNAME",
    status_column="COSTATUS",

    state="Colorado"
)

all_species.append(Colorado)


#
# conneticut
#

Connecticut = convert_species_csv(
    input_file="data/state_lists/ConnecticutEndThreat.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Connecticut"
)

all_species.append(Connecticut)

#
# Delaware
#

Delaware = convert_species_csv(
    input_file="data/state_lists/DelawareEndThreat.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Delaware"
)

all_species.append(Delaware)

#
# Florida
#

Florida = convert_species_csv(
    input_file="data/state_lists/florida_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Original Status",

    state="Florida"
)

all_species.append(Florida)

#
# Georgia
#

Georgia = convert_species_csv(
    input_file="data/state_lists/georgia_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Original Status",

    state="Georgia"
)

all_species.append(Georgia)

#
# Hawaii
#

#
# Kansas
#

Kansas = convert_species_csv(
    input_file="data/state_lists/kansas_species.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Original Status",

    state="Kansas"
)

all_species.append(Kansas)

# --------------------------------------------------
# Illinois
# --------------------------------------------------

illinois = convert_species_csv(
    input_file="data/state_lists/illinois_species.csv",
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
    input_file="data/state_lists/indiana_insects.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Species Name",
    status_column="STATE",

    state="Indiana"
)

all_species.append(Indiana)

Indiana = convert_species_csv(
    input_file="data/state_lists/indiana_plants.csv",
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
    input_file="data/state_lists/Iowa_anim.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Iowa"
)

all_species.append(Iowa)

Iowa = convert_species_csv(
    input_file="data/state_lists/Iowa_plns.csv",
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
    input_file="data/state_lists/kentucky.csv",
    #output_file="data/illinois_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Kentucky"
)

all_species.append(kentucky)


#
# Maine
#

Maine = convert_species_csv(
    input_file="data/state_lists/maine_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Maine"
)

all_species.append(Maine)

#
# Maryland
#

Maryland = convert_species_csv(
    input_file="data/state_lists/maryland_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Maryland"
)

all_species.append(Maryland)

#
# Massachusetts
#

Massachusetts = convert_species_csv(
    input_file="data/state_lists/massachusetts_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Massachusetts"
)

all_species.append(Massachusetts)

#---------------------------------------------------
# Michigan
# --------------------------------------------------

michigan = convert_species_csv(
    input_file="data/state_lists/michigan_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common name",
    scientific_name_column="Scientific name",
    status_column="status",

    state="Michigan"
)

all_species.append(michigan)

#
# Minnesota
#

minnesota = convert_species_csv(
    input_file="data/state_lists/minnesota_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Minnesota"
)

all_species.append(minnesota)

# --------------------------------------------------
# Missouri
# --------------------------------------------------

missouri = convert_species_csv(
     input_file="data/state_lists/missouri_threatened_endangered.csv",
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
     input_file="data/state_lists/mississippi_endangered_threatened.csv",
     #output_file="output/missouri_standardized.csv",

     common_name_column="Common Name",
     scientific_name_column="Scientific Name",
     status_column="State Status",

     state="Mississippi"
 )

all_species.append(mississippi)

#
# Montana
#

Montana = convert_species_csv(
     input_file="data/state_lists/montana_threatened_endangered.csv",
     #output_file="output/missouri_standardized.csv",

     common_name_column="name",
     scientific_name_column="scientific_name",
     status_column="status",

     state="Montana"
 )

all_species.append(Montana)

#
# Nebraska
#

Nebraska = convert_species_csv(
    input_file="data/state_lists/nebraska_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Nebraska"
)

all_species.append(Nebraska)

#
# Nevada
#

Nevada = convert_species_csv(
    input_file="data/state_lists/nevada.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="Nevada"
)

all_species.append(Nebraska)

#
# New_Hampshire
#

New_Hampshire = convert_species_csv(
    input_file="data/state_lists/new_hampshire_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="New Hampshire"
)

all_species.append(New_Hampshire)

#
# New Jersey
#

New_Jersey = convert_species_csv(
    input_file="data/state_lists/new_jersey_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="New Jersey"
)

all_species.append(New_Jersey)

#
# New Mexico
#

New_Mexico = convert_species_csv(
    input_file="data/state_lists/new_mexico_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="New Mexico"
)

all_species.append(New_Mexico)


#
# New York
#

New_York = convert_species_csv(
    input_file="data/state_lists/new_york_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="New York"
)

all_species.append(New_York)

#
# North Carolina
#

North_Carolina = convert_species_csv(
    input_file="data/state_lists/north_carolina_state_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="North Carolina"
)

all_species.append(North_Carolina)

#
# Ohio
#

Ohio = convert_species_csv(
    input_file="data/state_lists/ohio_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Ohio"
)

all_species.append(Ohio)

#
# Oklahoma
#

Oklahoma = convert_species_csv(
    input_file="data/state_lists/oklahoma.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Oklahoma"
)

all_species.append(Oklahoma)

#
# Oregon
#

Oregon = convert_species_csv(
    input_file="data/state_lists/oregon_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Oregon"
)

all_species.append(Oregon)

#
# rhode_island
#

rhode_island = convert_species_csv(
    input_file="data/state_lists/rhode_island_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="Rhode Island"
)

all_species.append(rhode_island)

#
# Pennsylvania
#

Pennsylvania = convert_species_csv(
    input_file="data/state_lists/Pennsylvania_cleaned.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Pennsylvania"
)

all_species.append(Pennsylvania)

#
# South Dakota
#

South_Dakota = convert_species_csv(
    input_file="data/state_lists/south_dakota_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="South Dakota"
)

all_species.append(South_Dakota)

#
# south_carolina
#

south_carolina = convert_species_csv(
    input_file="data/state_lists/south_carolina_endangered_animals.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="South Carolina"
)

all_species.append(south_carolina)

#
# Tennessee
#

Tennessee = convert_species_csv(
    input_file="data/state_lists/tennessee_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Tennessee"
)

all_species.append(Tennessee)

#
# Texas
#

Texas = convert_species_csv(
    input_file="data/state_lists/texas_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="State Status",

    state="Texas"
)

all_species.append(Texas)

#
# Vermont
#

Vermont = convert_species_csv(
    input_file="data/state_lists/vermont_species.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Vermont"
)

all_species.append(Vermont)

#
# Virginia
#

Virginia = convert_species_csv(
    input_file="data/state_lists/virginia_threatened_endangered.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="Virginia"
)

all_species.append(Virginia)

Virginia = convert_species_csv(
    input_file="data/state_lists/virginia_threatened_endangered_plants.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="name",
    scientific_name_column="scientific_name",
    status_column="status",

    state="Virginia"
)

all_species.append(Virginia)

#
# Washington
#

Washington = convert_species_csv(
    input_file="data/state_lists/washington_animals.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
    scientific_name_column="Scientific Name",
    status_column="Status",

    state="Washington"
)

all_species.append(Washington)

Washington = convert_species_csv(
    input_file="data/state_lists/washington_plants.csv",
    #output_file="data/federal_standardized.csv",

    common_name_column="Common Name",
        scientific_name_column="Scientific Name",
        status_column="Status",

    state="Washington"
)

all_species.append(Washington)

#
# Wisconsin
#

Wisconsin = convert_species_csv(
    input_file="data/state_lists/wisconsin.csv",
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

# Drop rows with no common name (habitat/area entries such as
# "Devil's Icebox Recharge Area", not actual species).
blank_names = master_list["Common Name"].isna() | (master_list["Common Name"].astype(str).str.strip() == "")
print(f"Removed {blank_names.sum()} rows with no common name")
master_list = master_list[~blank_names]

# County-level source lists repeat a species once per county, so keep one row
# per species per state (the first one seen).
total_before = len(master_list)
master_list = master_list.drop_duplicates(
    subset=["Scientific Name", "State"],
    keep="first"
).reset_index(drop=True)
print(f"Removed {total_before - len(master_list)} duplicate species/state rows")

master_list.to_csv(
    "data/master_species_list.csv",
    index=False
)

print()
print("====================================")
print("MASTER LIST CREATED")
print("====================================")
print(f"Total records: {len(master_list)}")
print("Saved to: data/master_species_list.csv")
