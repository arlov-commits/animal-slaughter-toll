#!/usr/bin/env python3
"""Build data.json for the slaughter clock.

Two FAOSTAT-derived land sources, plus a separate aquatic block:

  * WORLD / by-kind figures  ->  data/raw/world-data-six-year.csv
      15 species, one "slaughtered animals" head count per species per year
      2018..2024 (already de-duplicated of co-products and unit-corrected
      upstream — see CLAUDE.md "counting traps"). A final TOTAL row is NOT a
      species; we use it only to CHECK that the 15 sum to it per year.
      The site shows a chosen anchor year (2018..2024) or, by default, the
      plain arithmetic mean of 2022, 2023 and 2024 — computed HERE per species
      as (v2022+v2023+v2024)/3. The file's own "Three-year avg" / growth columns
      are deliberately ignored.

  * COUNTRY drill-down  ->  data/raw/animals_killed_by_species_country_year.csv
      Per-country head counts (FAOSTAT), anchored to 2023. We DROP the FAO
      "China" aggregate (351) and re-shape the per-country species onto the
      SAME 15-species taxonomy as the world file:
        - game and mammals_other are dropped from every country;
        - camels + other camelids merge into one "Camel (All Camelids)" row;
        - asses + mules merge into one "Donkeys & mules" row;
        - every other species is one-to-one.
      Per-country VALUES are otherwise unchanged — rows are only summed or
      removed. Any country-species label not in COUNTRY_TO_WORLD aborts the
      build, so a new or renamed label can never be silently lost or mis-bucketed.

  * AQUATIC ("sea") block  ->  config/sea_summary.csv  (unchanged; a separate
      fishcount.org.uk estimate range, never merged into the land figures).

Run from anywhere: `python3 scripts/build_data.py`. Paths resolve relative to
this file, so data.json is written to the repo root where index.html fetches it.
"""
import csv
import json
import os
import re
import datetime as dt
from collections import defaultdict

# Resolve paths relative to this script (scripts/ -> repo root), so the build
# works no matter the current working directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD_SRC = os.path.join(ROOT, "data", "raw", "world-data-six-year.csv")
COUNTRY_SRC = os.path.join(ROOT, "data", "raw", "animals_killed_by_species_country_year.csv")
SEA_SRC = os.path.join(ROOT, "config", "sea_summary.csv")
OUT = os.path.join(ROOT, "data.json")

CHINA_AGGREGATE = 351            # drop: equals mainland + HK + Macao + Taiwan
COUNTRY_YEAR = 2023              # the country drill-down is anchored here
WORLD_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
AVG_YEARS = [2022, 2023, 2024]   # the default basis = plain mean of these

# The 15 world species, in the world CSV's row order. Each maps the CSV "animal"
# label to a stable id, a display name and a land taxonomy group: avian (birds)
# vs terrestrial (the mammals). Display names keep the site's established forms;
# the two pre-grouped rows adopt the file's names verbatim.
#       csv_label,             id,                    display,                 group
WORLD_SPECIES = [
    ("Chicken",              "chickens",            "Chickens",              "avian"),
    ("Duck",                 "ducks",               "Ducks",                 "avian"),
    ("Pig",                  "pig",                 "Pigs",                  "terrestrial"),
    ("Goose",                "geese",               "Geese",                 "avian"),
    ("Sheep",                "sheep",               "Sheep",                 "terrestrial"),
    ("Rabbit/Hare",          "rabbits_hares",       "Rabbits & hares",       "terrestrial"),
    ("Goat",                 "goat",                "Goats",                 "terrestrial"),
    ("Turkey",               "turkeys",             "Turkeys",               "avian"),
    ("Cattle",               "cattle",              "Cattle",                "terrestrial"),
    ("Domestic Rodent",      "rodents_other",       "Other rodents",         "terrestrial"),
    ("Pigeon/Other Bird",    "pigeons_other_birds", "Pigeons & other birds", "avian"),
    ("Buffalo",              "buffalo",             "Buffalo",               "terrestrial"),
    ("Horse",                "horse",               "Horses",                "terrestrial"),
    ("Camel (All Camelids)", "camelids",            "Camel (All Camelids)",  "terrestrial"),
    ("Donkeys & mules",      "donkeys_mules",       "Donkeys & mules",       "terrestrial"),
]

# Re-shape the per-country FAO species labels onto the 15 world ids. None = drop
# the species from every country. The two merges sum their component rows per
# country; everything else is one-to-one. EVERY distinct label in the country
# CSV must appear here, or the build aborts.
COUNTRY_TO_WORLD = {
    "chickens":            "chickens",
    "ducks":               "ducks",
    "pig":                 "pig",
    "geese":               "geese",
    "sheep":               "sheep",
    "rabbits_hares":       "rabbits_hares",
    "goat":                "goat",
    "turkeys":             "turkeys",
    "cattle":              "cattle",
    "rodents_other":       "rodents_other",
    "pigeons_other_birds": "pigeons_other_birds",
    "buffalo":             "buffalo",
    "horse":               "horse",
    "camels":              "camelids",       # merge -> Camel (All Camelids)
    "camelids_other":      "camelids",       # merge -> Camel (All Camelids)
    "asses":               "donkeys_mules",  # merge -> Donkeys & mules
    "mules":               "donkeys_mules",  # merge -> Donkeys & mules
    "game":                None,             # drop
    "mammals_other":       None,             # drop
}


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def truthy(s):
    return str(s).strip().lower() == "true"


def slugify(name):
    """A clean lowercase id from a display name, matching the land-species id
    style (lowercase, '_'-separated): every run of non-alphanumerics collapses
    to one underscore. 'Wild-caught fish' -> 'wild_caught_fish'; 'Farmed
    molluscs (unnamed)' -> 'farmed_molluscs_unnamed'. The site's per-card image
    lookup turns '_' into '-' for the file name, so these resolve to
    img/species/wild-caught-fish.png etc. — the same convention as the land
    cards (e.g. id 'rabbits_hares' -> img/species/rabbits-hares.png)."""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def parse_world_value(s):
    """A world-CSV cell -> int head count.

    Cells arrive with surrounding spaces/quotes and comma thousands separators
    (e.g. ' 72,329,757,000 '); the csv module strips the quotes, we strip the
    rest. Empty -> None.
    """
    s = (s or "").strip().strip('"').strip().replace(",", "")
    if not s:
        return None
    return int(round(float(s)))


def load_world():
    """Read world-data-six-year.csv -> ({label: {year: int}}, total_row).

    Columns are matched by name after stripping the header's stray spaces; the
    avg/growth columns are never read. The TOTAL row is returned separately for
    the per-year sum check, never as a species.
    """
    with open(WORLD_SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader)]
        try:
            animal_idx = header.index("animal")
        except ValueError:
            raise SystemExit("world CSV: no 'animal' column")
        col = {}
        for y in WORLD_YEARS:
            key = "value_%d" % y
            if key not in header:
                raise SystemExit("world CSV: missing column %r" % key)
            col[y] = header.index(key)

        by_label, total_row = {}, None
        for raw in reader:
            if not raw or animal_idx >= len(raw):
                continue
            label = raw[animal_idx].strip()
            if not label:
                continue
            vals = {y: parse_world_value(raw[col[y]]) for y in WORLD_YEARS}
            if label.strip().upper() == "TOTAL":
                total_row = vals
            else:
                by_label[label] = vals
    if total_row is None:
        raise SystemExit("world CSV: no TOTAL row to check against")
    return by_label, total_row


def build_world():
    """Build the world species list (per-year counts) and run the TOTAL check.

    Returns (species_out, total_row, world_sums) where world_sums[year] is the
    sum of the 15 species in that year (== TOTAL row, verified here).
    """
    by_label, total_row = load_world()

    mapped = {lbl for (lbl, _, _, _) in WORLD_SPECIES}
    extra = set(by_label) - mapped          # an unmapped species row -> surface
    missing = mapped - set(by_label)
    if missing:
        raise SystemExit("world CSV: expected species missing: %s" % sorted(missing))
    if extra:
        raise SystemExit("world CSV: unmapped species row(s) %s — refusing to "
                         "silently drop. Add to WORLD_SPECIES." % sorted(extra))

    # 15 species must sum to the TOTAL row, every year (the file's own check).
    world_sums = {}
    for y in WORLD_YEARS:
        s = sum(by_label[lbl][y] for lbl in mapped)
        world_sums[y] = s
        if s != total_row[y]:
            raise SystemExit("world CSV: 15 species sum %d != TOTAL %d for %d"
                             % (s, total_row[y], y))

    species_out = [
        {
            "id": sid,
            "name": display,
            "group": group,
            "counts": {str(y): by_label[label][y] for y in WORLD_YEARS},
        }
        for (label, sid, display, group) in WORLD_SPECIES
    ]
    return species_out, total_row, world_sums


def build_countries():
    """Build the country drill-down, re-shaped onto the 15 world ids.

    Returns (countries_out, raw_by_country) — the second is the pre-merge
    per-country head counts keyed by ORIGINAL country-species label, kept only
    for the merge spot-check in the verification printout.
    """
    by_country = defaultdict(lambda: defaultdict(float))   # country -> world_id -> count
    raw_by_country = defaultdict(lambda: defaultdict(float))  # country -> orig label -> count
    country_code = {}
    seen_labels = set()

    with open(COUNTRY_SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            sp = r["species"]
            seen_labels.add(sp)
            if sp not in COUNTRY_TO_WORLD:
                raise SystemExit(
                    "country CSV: unmapped species label %r — refusing to guess. "
                    "Add it to COUNTRY_TO_WORLD." % sp)
            if int(r["area_code"]) == CHINA_AGGREGATE:
                continue
            if int(r["year"]) != COUNTRY_YEAR:
                continue
            v = num(r["animals_killed"])
            if v <= 0:
                continue
            target = COUNTRY_TO_WORLD[sp]
            country_code[r["country"]] = int(r["area_code"])
            raw_by_country[r["country"]][sp] += v
            if target is None:
                continue                       # dropped (game / mammals_other)
            by_country[r["country"]][target] += v

    countries_out = []
    for name, spd in by_country.items():
        total = sum(spd.values())
        countries_out.append(
            {
                "name": name,
                "code": country_code[name],
                "total": round(total),
                "by_species": {sp: round(v) for sp, v in spd.items() if v > 0},
            }
        )
    countries_out.sort(key=lambda c: c["total"], reverse=True)
    return countries_out, raw_by_country


def build_sea():
    """Build the aquatic-animal block from config/sea_summary.csv.

    These are fishcount.org.uk estimate RANGES (tonnage / mean weight), not FAO
    head counts, so each category carries a low and a high. The block is kept
    deliberately separate from the land data: it is never added to a land total
    and never appears in the country drill-down.

    The headline sea figure uses the LOW estimate. One row, feed_fish, is a
    SUBSET of wild-caught fish (counts_in_total = FALSE); it is carried on its
    own for footnote use and is never summed into the totals.
    """
    categories = []
    feed_fish = None
    with open(SEA_SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            entry = {
                # stable id/slug for the per-card image lookup (see slugify);
                # decoupled here so a card can find img/species/{id}.png the
                # same way land species do.
                "id": slugify(r["category"]),
                "category": r["category"],
                "group": r["group"],            # class group: fish / decapod / mollusc
                "fishery": r["fishery"],
                "sentience_tier": r["sentience_tier"],
                "year": int(r["year"]),
                "low": int(r["low"]),
                "high": int(r["high"]),
                "unit": r["unit"],
                "is_subset": truthy(r["is_subset"]),
                "counts_in_total": truthy(r["counts_in_total"]),
                "source": r["source"],
                "note": r["note"],
            }
            if entry["counts_in_total"]:
                categories.append(entry)
            else:
                # The lone subset row (feed fish). Carried for footnote use
                # only — kept out of `categories` so it can never be summed in.
                feed_fish = entry

    total_low = sum(c["low"] for c in categories)    # headline basis
    total_high = sum(c["high"] for c in categories)

    return {
        "meta": {
            "source": "fishcount.org.uk (A. Mood & P. Brooke)",
            "method": "FAO capture & aquaculture production tonnage divided by "
            "estimated mean weight per species — every figure is a RANGE, not a "
            "head count (unlike the land/FAO data).",
            "headline_basis": "low",
            "unit": "individuals",
            "note": "Aquatic animals killed for food, as estimate ranges. Kept "
            "SEPARATE from the land data: not part of any land total and not in "
            "the country breakdown. The headline uses the LOW estimate; high is "
            "carried for range display. feed_fish is a SUBSET of wild-caught "
            "fish (counts_in_total=false) — a footnote only, never added.",
        },
        "total_low": total_low,
        "total_high": total_high,
        "categories": categories,
        "feed_fish": feed_fish,
    }


def avg3(counts):
    """Plain arithmetic mean of the AVG_YEARS values (floats kept)."""
    return sum(counts[str(y)] for y in AVG_YEARS) / len(AVG_YEARS)


def main():
    species_out, total_row, world_sums = build_world()
    countries_out, raw_by_country = build_countries()

    data = {
        "meta": {
            "land_source": "FAOSTAT — Crops and livestock products, "
            "Producing/Slaughtered animals",
            "source_url": "https://www.fao.org/faostat/en/#data/QCL",
            "world_years": WORLD_YEARS,
            "avg_years": AVG_YEARS,
            "default_year": "avg",
            "country_reference_year": COUNTRY_YEAR,
            "generated": dt.date.today().isoformat(),
            "breaths_per_minute": 15,
            "note": "Land animals slaughtered for food worldwide. The world / "
            "by-kind figures are a 15-species FAOSTAT series, selectable by year "
            "(2018–2024) or shown as the plain 2022–2024 average by default. The "
            "country drill-down is the sum of reporting countries for "
            + str(COUNTRY_YEAR)
            + ", re-shaped to the same 15 species (the FAO 'China' aggregate is "
            "excluded to avoid double counting). Figures count individual "
            "animals, not biomass.",
        },
        # Year-selection policy lives in the data, not the UI: which years can be
        # chosen, which years the default average spans, and that the default is
        # that average.
        "world": {
            "years": WORLD_YEARS,
            "avg_years": AVG_YEARS,
            "default": "avg",
        },
        "species": species_out,
        "countries": countries_out,
    }

    # Aquatic animals — a structurally separate block (see build_sea).
    data["sea"] = build_sea()

    # Card ids must be unique and disjoint across land + sea, since the UI keys
    # cards (and their image lookup) on a single id namespace. Abort on a clash
    # rather than let one card's image/rate shadow another's.
    land_ids = [sp["id"] for sp in species_out]
    sea_ids = [c["id"] for c in data["sea"]["categories"]]
    all_ids = land_ids + sea_ids
    dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
    if dupes:
        raise SystemExit("card id collision across land/sea: %s" % dupes)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # ---- verification printout -------------------------------------------------
    sea = data["sea"]
    avg_total = sum(avg3(sp["counts"]) for sp in species_out)
    print(f"Wrote {OUT}")
    print(f"  world species : {len(species_out)}  (sum to TOTAL row, all years OK)")
    print(f"  countries     : {len(countries_out)}")
    print(f"  country year  : {COUNTRY_YEAR}")
    print("  world totals per selectable year (15 species == TOTAL row):")
    for y in WORLD_YEARS:
        print(f"      {y}: {world_sums[y]:>15,}   (TOTAL row {total_row[y]:>15,})")
    print(f"  default 3-yr avg ({'+'.join(map(str, AVG_YEARS))})/3 total: "
          f"{round(avg_total):>15,}")
    print(f"  sea cats      : {len(sea['categories'])} counted + feed_fish (subset, excluded)")
    print(f"  sea low       : {sea['total_low']:,}  (headline basis)")
    print("  sea card ids -> image file:")
    for c in sea["categories"]:
        print(f"      {c['category']:<28} {c['id']:<26} img/species/{c['id'].replace('_', '-')}.png")


if __name__ == "__main__":
    main()
