# Killed for food — a live count

A static, single-page memorial that counts up, in real time, the number of
**land animals slaughtered for food worldwide**. Somber by design — an
inscription, not a dashboard.

It shows the running total so far this calendar year, the pace of the killing
at every scale (per year, month, day, hour, minute, second, and breath), and a
breakdown by species that drills down into individual countries.

**Live site:** enable GitHub Pages (see below).

## What it shows

- A live counter of animals killed **so far this year**, plus a quieter count
  of how many have died **since you opened the page**.
- The pace at seven time scales, down to **per breath** (a placeholder of
  15 breaths per minute — change `breaths_per_minute` in `scripts/build_data.py`).
- **By species:** all 19 FAO species, ranked, each expandable to its leading
  countries.
- A scope selector to recompute the entire clock **for a single country**.

## Data & method

Source: [**FAOSTAT**](https://www.fao.org/faostat/en/#data/QCL) — the UN Food
and Agriculture Organization's "Crops and livestock products" data, the
*Producing / Slaughtered animals* element. Figures count individual animals.

The clock is built from `animals_killed_by_species_country_year.csv` by
`build_data.py`, which:

- **Drops the FAO "China" aggregate (area code 351)**, which equals the sum of
  China mainland, Hong Kong, Macao, and Taiwan — all present separately — so
  nothing is counted twice.
- Anchors every series to the **latest complete year, 2023** (FAO's 2024 data
  is still partial and treated as incomplete); the two minor "game" / "other
  mammals" series end in 2017 and fall back to their own latest year.
- Computes each country's figure in that same reference year, so country totals
  sum exactly to the world total.

The result, **~86.08 billion land animals per year**, is written to `data.json`.

### Honest caveats (stated on the page)

These are *land* animals killed for food. They **exclude** fish and other
aquatic animals — by number the largest group of all — as well as animals who
die before slaughter, the day-old male chicks culled at hatcheries, and animals
killed outside recorded food production. The real toll is higher. The live
figures are a steady rate spread evenly across the year, not a moment-by-moment
feed.

## Rebuilding the data

```bash
python3 scripts/build_data.py   # reads data/raw/…csv, writes data.json
```

No third-party Python packages are required.

## Running locally

The page fetches `data.json`, so open it through a web server (not `file://`):

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Enabling GitHub Pages

1. Merge this work into the branch you want to publish (e.g. `main`).
2. Repository **Settings → Pages**.
3. **Source:** "Deploy from a branch"; pick the branch and the `/ (root)`
   folder.
4. The site goes live at `https://<user>.github.io/animal-slaughter-toll/`.

`.nojekyll` is included so Pages serves every file verbatim.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The entire site — markup, style, and logic in one file. |
| `data.json` | Generated figures the page loads (served from root). |
| `scripts/build_data.py` | Rebuilds `data.json` from the FAOSTAT CSV. |
| `data/raw/animals_killed_by_species_country_year.csv` | Primary source data (the only CSV the build reads). |
| `data/raw/reference/` | FAOSTAT reference tables (codes, elements, flags) kept for provenance; see `data/README.md`. |
| `.nojekyll` | Tells GitHub Pages to skip Jekyll processing. |
