# Data

This folder holds the species data behind EcoRisk AI's protected-species check, and the state boundary shapefile used to work out which state(s) a search area touches.

```
data/state_lists/  ──create_master_list.py──▶  master_species_list.csv  ──taxon_lookup.py──▶  MasterTaxonLookup.csv
(one or more CSVs per state + federal)                                      (+ Taxon.tsv from GBIF)
```

| Path | What it is | In git? |
|---|---|---|
| `state_lists/` | Raw endangered/threatened lists, one or more CSVs per state, plus the federal (FWS) list. Every source has its own column names. | Yes |
| `master_species_list.csv` | All of the above standardized into one file: `Common Name, Scientific Name, Status, State`. Federal rows use `State` = `All`. | Yes |
| `MasterTaxonLookup.csv` | `master_species_list.csv` plus a `Taxon Key` column (the GBIF ID). **This is the only species file the app reads** (see `GBIF.py`). | Yes |
| `Taxon.tsv` | GBIF's backbone taxonomy dump. Only needed to rebuild `MasterTaxonLookup.csv`. | **No** (too large) |
| `cb_2022_us_state_20m/` | Census Bureau state boundary shapefile used by `scripts/state_lookup.py`. Geometry only, unrelated to the species pipeline. | See the main [README](../README.md#requirements) |

You only need to follow this guide to refresh or extend the species data. To just run the app, `MasterTaxonLookup.csv` is already checked in.

---

## Rebuilding the data

All commands run from the **project root**, with the project's Python environment active (see the main [README](../README.md#requirements)).

### 1. Collect the state lists (outside this repo)

Scrape or download each state's endangered/threatened list, plus the federal list, and put the CSVs in `data/state_lists/`.

> The scrapers we used to produce these files are not included in this repo, so this step is manual for now.

### 2. Download the GBIF backbone

Download the **GBIF Backbone Taxonomy** from [gbif.org](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c), unzip it, and place `Taxon.tsv` in `data/`. It is several GB, which is why it isn't committed.

### 3. Build the master list

```
python scripts/create_master_list.py
```

Reads every file listed in the script, standardizes the columns, keeps only rows whose status maps to **Endangered** or **Threatened**, and writes `data/master_species_list.csv`. Along the way it:

- drops rows with **no common name** (habitat/area entries such as "Devil's Icebox Recharge Area", not real species)
- removes **duplicate rows for the same species and state** (several source lists repeat a species once per county)

It prints how many rows each step removed.

> **Warning: expect a little stray data.** The state lists come from scrapers that aren't perfect, so the master list can contain a few rows that aren't real species or have mangled text (for example, a common name with a stray comma or quote that splits a row). You can find and fix the obvious ones by hand in `master_species_list.csv`, but leaving them in does little harm: a row that doesn't match a real GBIF species just gets no taxon key in step 4 and is ignored by scans. Re-running step 3 overwrites any manual edits, so do cleanup after it.

### 4. Build the taxon lookup

```
python scripts/taxon_lookup.py
```

Matches each scientific name in `master_species_list.csv` against `data/Taxon.tsv` (no network calls) and writes `data/MasterTaxonLookup.csv`, the same columns plus `Taxon Key`. It prints how many rows matched and lists every scientific name it couldn't match. Unmatched rows are written with a blank key, and the app skips those.

Commit the updated `master_species_list.csv` and `MasterTaxonLookup.csv`.

---

## Adding a state or list

1. Put the CSV in `data/state_lists/`. Use the exact filename, since paths are case-sensitive on Linux.
2. In `scripts/create_master_list.py`, copy an existing block and fill in:
   - `input_file`: the path to your CSV
   - `common_name_column`, `scientific_name_column`: that file's column names
   - `status_column`: the column holding the listing status
   - `state`: the state's full name (e.g. `"Illinois"`), or `"All"` for federal
3. Append the result with `all_species.append(...)`.
4. Re-run steps 3 and 4 above.

Status values are standardized by `normalize_status` in `scripts/normalize_func.py`. Labels like `E`, `LE`, `SE`, `Endangered` and `T`, `LT`, `ST`, `Threatened` are recognized. Anything else (candidate, special concern, rare, and so on) is dropped. If a new list uses an unusual label, add it there.

---

<<<<<<< HEAD
=======
## Current Data

Use the following data and links if they are still active to easily retreive the necassary data


  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  State                   Source                                                                                                                                                                   Notes
  ----------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ -----------------------
  Alabama                 [Alabama Administrative Code 220-2-.92](https://admincode.legislature.state.al.us/administrative-code/220-2-.92)                                                         

  Alaska                  [Alaska Department of Fish and Game --- ESA-listed species](https://www.adfg.alaska.gov/index.cfm?adfg=wildlifediversity.esalisted&id=esa-general-information)           

  Arizona                 [Arizona Game and Fish --- Species List](https://hdms.azgfd.com/species-list/species/)                                                                                   

  Arkansas                [Arkansas Game and Fish Commission --- Code of                                                                                                                           
                          Regulations](https://www.agfc.com/resources/code-of-regulations/browse/collections/e097609a-4ef1-459f-98e2-5532730099f6/policies/e48bd3be-33ce-4706-ab1e-ebde973779e9)   

  California              [California Endangered Species Act](https://wildlife.ca.gov/Conservation/CESA)                                                                                           

  Colorado                [Colorado Parks and Wildlife --- Threatened and Endangered Wildlife](https://cpw.state.co.us/threatened-and-endangered-wildlife)                                         Source was marked as
                                                                                                                                                                                                   uncertain.

  Connecticut             [Connecticut DEEP --- Endangered Species Listings](https://portal.ct.gov/DEEP/Endangered-Species/Endangered-Species-Listings?utm_source=chatgpt.com&archived=true)       

  Delaware                [Delaware DNREC species data](https://dnrec.delaware.gov/dewap/data/species?$top=100&$skip=0)                                                                            

  Florida                 [Florida Fish and Wildlife --- State Listing](https://myfwc.com/wildlifehabitats/wildlife/state-listing/)                                                                

  Georgia                 [Georgia Rules and Regulations 391-4-10-.09](https://rules.sos.ga.gov/gac/391-4-10-.09)                                                                                  

  Hawaii                  ---                                                                                                                                                                      No suitable source was
                                                                                                                                                                                                   found.

  Idaho                   Federal list                                                                                                                                                             Use the federal list.

  Illinois                [Illinois Endangered and Threatened Species Program](https://naturalheritage.illinois.gov/speciesconservation/endangeredandthreatenedspeciesprogram.html)                

  Indiana                 [Indiana DNR --- Endangered Plant and Animal Species](https://www.in.gov/dnr/nature-preserves/heritage-data-center/endangered-plant-and-animal-species/)                 

  Indiana (additional     [Indiana endangered, threatened, and rare plants PDF](https://www.in.gov/dA/02bd3906ef/np-etrplants.pdf?language_id=1)                                                   Additional source.
  plant source)                                                                                                                                                                                    

  Iowa                    [Iowa DNR --- Threatened and Endangered Wildlife](https://www.iowadnr.gov/programs-services/iowas-wildlife/threatened-endangered-wildlife)                               

  Kansas                  [Kansas Threatened and Endangered                                                                                                                                        
                          Species](https://www.ksoutdoors.gov/programs-services/conservation-ecological-services/threatened-endangered-species-in-need-of-conservation)                            

  Kentucky                [Kentucky species database](https://app.fw.ky.gov/speciesOb)                                                                                                             

  Louisiana               [Louisiana --- Rare Species and Natural Communities by Parish](https://www.wlf.louisiana.gov/page/rare-species-and-natural-communities-by-parish)                        

  Maine                   [Maine --- Listed Species](https://www.maine.gov/ifw/fish-wildlife/wildlife/endangered-threatened-species/listed-species.html)                                           

  Maryland                [Maryland DNR --- Rare, Threatened, and Endangered Animals](https://dnr.maryland.gov/wildlife/Pages/plants_wildlife/rte/rteanimals.aspx)                                 

  Massachusetts           [Massachusetts --- Endangered, Threatened, and Special Concern Species](https://www.mass.gov/info-details/list-of-endangered-threatened-and-special-concern-species)     

  Michigan                [Michigan --- Threatened and Endangered Species                                                                                                                          
                          List](https://www.michigan.gov/dnr/managing-resources/wildlife/wildlife-permits/threatened-endangered-species/threatened-and-endangered-species-list)                    

  Minnesota               [Minnesota DNR --- Endangered, Threatened, and Special Concern Species](https://www.dnr.state.mn.us/ets/index.html)                                                      

  Mississippi             [Mississippi Endangered Species](https://www.mdwfp.com/museum-natural-science/mississippi-endangered-species)                                                            

  Missouri                [Missouri Natural Heritage Program](https://mdc.mo.gov/your-property/responsible-construction/missouri-natural-heritage-program)                                         State endangered
                                                                                                                                                                                                   species source.

  Montana                 [Montana Natural Heritage Program --- Species of Concern](https://mtnhp.org/SpeciesOfConcern/)                                                                           G1/S1 and G2/S2 ranks
                                                                                                                                                                                                   were treated as
                                                                                                                                                                                                   endangered because of
                                                                                                                                                                                                   the associated risk
                                                                                                                                                                                                   levels.

  Nebraska                [Nebraska Natural Heritage Program](https://outdoornebraska.gov/conservation/conservation-efforts/natural-heritage-program/)                                             

  Nevada (source 1)       [Nevada Administrative Code 527](https://www.leg.state.nv.us/Division/Legal/LawLibrary/NAC/NAC-527.html)                                                                 

  Nevada (source 2)       [Nevada Administrative Code 503](https://www.leg.state.nv.us/nac/nac-503.html?utm_source=chatgpt.com)                                                                    

  New Hampshire           [New Hampshire --- Endangered and Threatened                                                                                                                             
                          Wildlife](https://www.wildlife.nh.gov/wildlife-and-habitat/nongame-and-endangered-species/endangered-and-threatened-wildlife-nh)                                         

  New Jersey              [New Jersey Fish and Wildlife --- Endangered, Threatened, and Special Concern                                                                                            
                          Species](https://dep.nj.gov/njfw/wildlife/endangered-threatened-and-special-concern-species/)                                                                            

  New Mexico              [New Mexico --- Threatened and Endangered Species](https://wildlife.dgf.nm.gov/conservation/wildlife-species-information/threatened-and-endangered-species/)             

  New York                [New York DEC --- Endangered Species List](https://dec.ny.gov/nature/animals-fish-plants/biodiversity-species-conservation/endangered-species/list)                      

  North Carolina          [North Carolina --- Species Conservation Plans](https://www.ncwildlife.gov/wildlife-habitat/species-conservation-plans)                                                  

  North Dakota            [North Dakota Game and Fish --- Endangered Species](https://gf.nd.gov/ecology/endangered)                                                                                Use the federal list.

  Ohio                    [Ohio DNR --- State-listed Species](https://ohiodnr.gov/discover-and-learn/safety-conservation/about-ODNR/wildlife/state-listed-species)                                 

  Oklahoma                [Oklahoma --- Threatened and Endangered Species](https://www.wildlifedepartment.com/wildlife/threatened-and-endangered)                                                  Source was marked as
                                                                                                                                                                                                   uncertain.

  Oregon                  [Oregon --- Threatened, Endangered, and Candidate Species](https://www.dfw.state.or.us/wildlife/diversity/species/threatened_endangered_candidate_list.asp)              

  Pennsylvania            [Pennsylvania Game Commission --- Endangered and Threatened Species](https://www.pa.gov/agencies/pgc/wildlife/discover-pa-wildlife/endangered-and-threatened)            

  Rhode Island            [Rhode Island Natural History Survey --- Rare Species](https://rinhs.org/species/rare-species/)                                                                          

  South Carolina (source  [South Carolina Regulation 123-150-2](https://regulations.justia.com/states/south-carolina/chapter-123/article-5/section-123-150-2/)                                     
  1)                                                                                                                                                                                               

  South Carolina (source  [South Carolina Regulation R. 123-150](https://www.law.cornell.edu/regulations/south-carolina/R-123-150)                                                                 
  2)                                                                                                                                                                                               

  South Dakota            [South Dakota --- Threatened and Endangered Species](https://gfp.sd.gov/threatened-endangered/)                                                                          

  Tennessee (source 1)    [Tennessee Secretary of State --- Rules](https://publications.tnsosfiles.com/rules/1660/1660.htm)                                                                        

  Tennessee (source 2)    [Tennessee Wildlife Resources Agency --- Wildlife](https://www.tn.gov/content/tn/twra/wildlife.html)                                                                     

  Texas                   [Texas Parks and Wildlife --- Listed Species](https://tpwd.texas.gov/wildlife/wildlife-diversity/nongame/listed-species/)                                                

  Utah                    [Utah Species Protection](https://wildlife.utah.gov/speciesprotection)                                                                                                   Use the federal list.

  Vermont                 [Vermont Fish and Wildlife --- Endangered and Threatened Species](https://www.vtfishandwildlife.com/conserve/endangered-and-threatened-species)                          

  Virginia                [Virginia Administrative Code --- 2VAC5-320-10](https://law.lis.virginia.gov/admincode/title2/agency5/chapter320/section10/)                                             

  Washington              [Washington Department of Fish and Wildlife --- Listed Species](https://wdfw.wa.gov/species-habitats/at-risk/listed)                                                     

  West Virginia           [West Virginia DNR --- Rare, Threatened, and Endangered Species](https://wvdnr.gov/plants-animals/rare-threatened-endangered-species/)                                   Use the federal list.

  Wisconsin               [Wisconsin DNR --- Wisconsin Natural Heritage Inventory](https://dnr.wisconsin.gov/topic/NHI/WList)                                                                      

  Wyoming                 [BLM --- Wyoming Threatened and Endangered Species Data](https://www.blm.gov/programs/fish-and-wildlife/threatened-and-endangered/state-te-data/wyoming)                 Use the federal list.
  
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

>>>>>>> f1486682b6d3a62535ff1b7b252190b01422f960
## Known issues and open items

- `state_lists/Indiana_anim.csv` is not used. Its scientific names have the spaces stripped (`Megachileintegra`), so none of them could match GBIF. It needs a corrected export.
- `state_lists/missouri.csv` is not used. It's the full county list, and the file the script does use (`missouri_threatened_endangered.csv`) contains exactly its endangered rows.
- Only states present in `MasterTaxonLookup.csv` can be flagged. For a state with no list, sightings still count toward the total species figure, but nothing there is marked protected.
- Listings are matched at the species level. GBIF often reports a species where a state lists a subspecies or variety, in which case the species-level sighting is used.
