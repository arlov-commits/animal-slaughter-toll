# Sea animals — data methodology & notes

Source: **fishcount.org.uk** (A. Mood & P. Brooke), the leading public estimator of
aquatic animals killed by humans for food. Their recent estimates are peer-reviewed
(journal *Animal Welfare*, 2023/2024). Numbers are derived from FAO capture &
aquaculture production **tonnages** divided by **estimated mean weights (EMW)** per
species — so every figure is a RANGE, not a precise count. This is fundamentally
different from the land-animal data (FAO reports actual head counts there).

## Project framing (important)
We quantify the **human-caused killing rate** — animals caught or slaughtered BY humans
for food. Not natural mortality. This is why marine mammals (dolphins, whales) are
excluded (not in FAO fishery production) and why fishcount's caught/slaughtered framing
fits our thesis exactly.

## Headline figures used (latest fishcount, ~2022) -> see sea_summary.csv
All counted in the sea total EXCEPT feed-fish (footnote only):

| Category | Low | High | Year |
|---|---|---|---|
| Wild-caught fish | 787 B | 2,328 B | 2007-2016 avg (extended to 2003-2022) |
| Farmed fish | 86 B | 181 B | 2022 (central ~133B) |
| Farmed crustaceans | 310 B | 950 B | 2022 (central ~630B) |
| Farmed bivalves | 360 B | 900 B | 2022 |
| Farmed gastropods | 4.1 B | 8.8 B | 2022 |
| Farmed molluscs (unnamed) | 31 B | 95 B | 2022 |

**Sea total (excl. feed-fish): ~1.58 trillion (low) to ~4.46 trillion (high) per year.**
For comparison, land animals are ~104 billion/year. **Sea is ~15x land even at the floor.**
Per the project's "use the minimum for the main figure" rule, the headline sea number is ~1.58T.

## Feed-fish — the one real overlap (FOOTNOTE ONLY, never added)
~460-1,100 B wild fish are caught and ground into fishmeal/oil, mostly to feed farmed
fish. These are a **SUBSET of wild-caught fish**, not additional animals — adding them
would double-count. Shown as context/footnote only (`counts_in_total = FALSE`).

## Filter-feeder footnote (NO overlap with caught-fish count)
Farmed bivalves are filter-feeders. fishcount estimates each mussel eats ~120 tiny
animals/day, so 360-900B farmed bivalves consumed an estimated **7.8-79 QUADRILLION**
tiny creatures (zooplankton etc.). These are eaten BY the mussels, never caught or
reported by humans — they are NOT in the wild-caught category and there is no overlap to
exclude. This is a provocative footnote at the edge of the "human killing rate" thesis
(is mussel-filter-feeding human-caused killing?), NOT a counted figure.

## Sentience tiers (the ethical axis) — fishcount supports this distinction
fishcount is explicit: strong evidence that **finfish, decapod crustaceans, and
cephalopods are sentient**; but **almost no studies on bivalve sentience**, and bivalve
farming is "arguably more welfare-friendly" (sessile filter-feeders). So our tiering:
- `evidence_sentient`: finfish, decapods, cephalopods
- `open_question`: bivalves (mussels, oysters, clams, scallops) — precautionary
- `low_evidence` / `mollusc_other`: gastropods, unclassified molluscs
Cephalopods (octopus) are EXCLUDED from farmed totals — FAO reports no 2022 farmed
octopus tonnage (farming still experimental). Not an omission to "fix."

## Detail layer -> see sea_species_detail.csv (via parse_clean_sheets.py)
Per-species/class detail for custom class / size-tier / sentience groupings.
Parsed ONLY from clean sheets:
- Wild-fish `GEMWs` sheet: per-class summary. **WARNING: its numbers sum to only
  ~453-1,153 B — roughly HALF the true wild total — because species with specific
  (non-generic) mean weights live in the messy 12,000-row Sheet1. Treat the class
  numbers as ILLUSTRATIVE of distribution, NOT as the wild total.** (Verified: class-sum
  453B-1.15T vs published 787B-2.33T.)
- 2020-22 mollusc & crustacean files: clean per-species rows. **Verified accurate** —
  mollusc species sum to 389-1,004 B, matching fishcount's published 390-1,000 B.

Size tiers (by mean weight): tiny <20g, small <200g, medium <2000g, large >=2000g.
Of 373 farmed aquatic species: 187 tiny, 171 small, only 17 medium+large — most farmed
aquatic animals are very small, which matters for the "are these equivalent to a cow?"
question your groupings will surface.

## DELIBERATELY NOT USED (avoid the rabbit hole)
- 2017 farmed-fish/decapod spreadsheets: booby-trapped with (a)-(e) lettered SUBTOTAL
  rows and stacked tables; outdated. Use the prose headline figures (sea_summary.csv).

## TRENDS OVER TIME — a SEPARATE future data-pull
These spreadsheets are SNAPSHOTS (wild = one 2007-2016 average; 2017 files = single year;
only mollusc/crustacean have 3 years). They CANNOT produce a good trend line. fishcount's
prose says per-year wild data exists for 2003-2022, and farmed fish grew nine-fold since
1990 — but that time series lives in their newer papers/site, not these downloads. To do
"slaughter vs human population over time," pull that data later (or hand-clean it). Parsing
these 5 files harder will NOT yield trends.
