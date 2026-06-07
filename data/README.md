# data/

Raw inputs for the slaughter clock. Nothing here is served by the site;
`scripts/build_data.py` reads from here and writes `data.json` to the repo root.

## `raw/animals_killed_by_species_country_year.csv`

The **only** file the build consumes. One row per species × country × year, with
columns `area_code, country, species, year, animals_killed, Flag`. Derived from
FAOSTAT's *Crops and livestock products* dataset (the *Producing /
Slaughtered Animals* element), counting individual land animals.

## `raw/reference/` — FAO code-lookup tables (provenance only)

Thirteen FAOSTAT metadata/code tables, kept so the primary CSV's codes can be
traced back to source. **None are read by the build or the site.** The eight
`FAOSTAT_data_6-5-2026 (1..8).csv` files are near-duplicate metadata dumps
(item codes, element codes, flags, glossaries, country codes/groups); the four
`Production_Crops_Livestock_E_*.csv` files are the area / element / flag / item
code tables.

Source: [FAOSTAT](https://www.fao.org/faostat/en/#data/QCL). These are
reference-only and could be removed without affecting the build — see the open
question about gitignoring them.
