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
- **By species:** all 15 FAO species, ranked, each expandable to its leading
  countries.
- A scope selector to recompute the entire clock **for a single country**.
- A **year selector** for the world figures — any year **2018–2024**, or the
  default **2022–2024 average**; the whole clock recomputes from the choice.

## Data & method

Source: [**FAOSTAT**](https://www.fao.org/faostat/en/#data/QCL) — the UN Food
and Agriculture Organization's "Crops and livestock products" data, the
*Producing / Slaughtered animals* element. Figures count individual animals.

The clock is built from two land CSVs by `build_data.py`, which:

- Takes the **world / by-kind** figures from `world-data-six-year.csv` — 15
  species × years **2018–2024** — and checks the 15 sum to the file's `TOTAL`
  row each year. The default basis is the **plain mean of 2022–2024**, computed
  per species (the file's own average column is ignored).
- Builds the **country drill-down** from
  `animals_killed_by_species_country_year.csv` at **2023**, after **dropping the
  FAO "China" aggregate (area code 351)** — which equals China mainland +
  Hong Kong + Macao + Taiwan, all present separately — so nothing is counted
  twice.
- **Re-shapes the per-country species onto the same 15-species taxonomy**:
  `game` and `mammals_other` are dropped; `camels` + `camelids_other` merge into
  *Camel (All Camelids)*; `asses` + `mules` merge into *Donkeys & mules*. Values
  are otherwise unchanged — rows are only summed or removed.

The result — a world headline of **~86.3 billion (2023)** / **~87.9 billion
(2024)** / **~86.28 billion (2022–2024 average)**, with a separate **~86.08
billion** country-sum for the 2023 drill-down — is written to `data.json`.

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
| `scripts/build_data.py` | Rebuilds `data.json` from the FAOSTAT CSVs. |
| `data/raw/world-data-six-year.csv` | World / by-kind source: 15 species × years 2018–2024. |
| `data/raw/animals_killed_by_species_country_year.csv` | Per-country source for the drill-down (re-shaped to the 15 species). |
| `data/raw/reference/` | FAOSTAT reference tables (codes, elements, flags) kept for provenance; see `data/README.md`. |
| `.nojekyll` | Tells GitHub Pages to skip Jekyll processing. |
