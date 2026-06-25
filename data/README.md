# data/

Raw inputs for the slaughter clock. Nothing here is served by the site;
`scripts/build_data.py` reads from here and writes `data.json` to the repo root.

## `raw/world-data-six-year.csv`

The **world / by-kind** source. One row per species (15 of them) with a head
count for each year **2018–2024**, plus average/growth columns the build
**ignores** and a final `TOTAL` row used **only as a check** (the 15 species must
sum to it each year). Values carry comma thousands-separators and stray
spaces/quotes — parsed robustly. The two pre-grouped rows *Camel (All Camelids)*
and *Donkeys & mules* are adopted as-is. This file drives the site's world view,
the terrestrial/avian kind split, and the year selector.

## `raw/animals_killed_by_species_country_year.csv`

The **per-country drill-down** source. One row per species × country × year, with
columns `area_code, country, species, year, animals_killed, Flag`. Derived from
FAOSTAT's *Crops and livestock products* dataset (the *Producing /
Slaughtered Animals* element), counting individual land animals. The build takes
**2023**, drops the FAO "China" aggregate (351), and re-shapes the per-country
species onto the **same 15-species taxonomy** as the world file (drop `game` and
`mammals_other`; merge `camels`+`camelids_other` and `asses`+`mules`).

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
