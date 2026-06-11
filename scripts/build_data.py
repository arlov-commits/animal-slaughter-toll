#!/usr/bin/env python3
"""Build data.json for the slaughter clock from FAOSTAT data.

Source: data/raw/animals_killed_by_species_country_year.csv (FAOSTAT,
"Producing Animals/Slaughtered" element). Each row is animals slaughtered for
food of a given species, in a country, in a year.

Run from anywhere: `python3 scripts/build_data.py`. Paths are resolved
relative to this file, so the CSV is read from data/raw/ and data.json is
written to the repo root (where index.html fetches it).

Method (kept deliberately conservative and reproducible):

  * The FAO area "China" (code 351) is an aggregate of China mainland,
    Hong Kong, Macao and Taiwan, all of which are also present as their own
    rows. We DROP code 351 so nothing is counted twice.
  * We anchor every series to 2023, the latest complete year. (FAO's 2024
    figures are still being revised and are treated as incomplete.) The two
    negligible "game" / "other mammals" series stop in 2017, so they fall
    back to their own most recent year.
  * A country's figure for a species is its value in that same reference
    year (absent = 0). Country figures therefore sum exactly to the world
    total.
  * Aquatic animals (the "sea" block) come from a SEPARATE source,
    config/sea_summary.csv (fishcount.org.uk estimate ranges, not FAO head
    counts). They are carried alongside the land data but never merged into
    world_total or the country breakdown. The subset row feed_fish
    (counts_in_total=false) is carried for footnote use only — never summed.
"""
import csv
import json
import os
import datetime as dt
from collections import defaultdict

# Resolve paths relative to this script (scripts/ -> repo root), so the build
# works no matter the current working directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "animals_killed_by_species_country_year.csv")
SEA_SRC = os.path.join(ROOT, "config", "sea_summary.csv")
OUT = os.path.join(ROOT, "data.json")
CHINA_AGGREGATE = 351  # drop: equals mainland + HK + Macao + Taiwan
TARGET_YEAR = 2023      # anchor year; 2024 is still treated as incomplete

# Plain-language names; FAO uses terse / mixed singular labels.
DISPLAY = {
    "chickens": "Chickens",
    "ducks": "Ducks",
    "pig": "Pigs",
    "geese": "Geese",
    "sheep": "Sheep",
    "rabbits_hares": "Rabbits & hares",
    "goat": "Goats",
    "turkeys": "Turkeys",
    "cattle": "Cattle",
    "rodents_other": "Other rodents",
    "pigeons_other_birds": "Pigeons & other birds",
    "buffalo": "Buffalo",
    "horse": "Horses",
    "camels": "Camels",
    "camelids_other": "Other camelids",
    "asses": "Donkeys",
    "game": "Game",
    "mammals_other": "Other mammals",
    "mules": "Mules",
}

# Birds in the FAO land data; every other land species is a (terrestrial)
# mammal. Used by the site to split the land figures into avian / terrestrial
# scopes — a taxonomy lives here in the data layer, never in the UI.
AVIAN = {"chickens", "ducks", "geese", "turkeys", "pigeons_other_birds"}


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def truthy(s):
    return str(s).strip().lower() == "true"


def build_sea():
    """Build the aquatic-animal block from config/sea_summary.csv.

    These are fishcount.org.uk estimate RANGES (tonnage / mean weight), not FAO
    head counts, so each category carries a low and a high. The block is kept
    deliberately separate from the land data: it is never added to world_total
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
            "SEPARATE from the land data: not part of world_total and not in the "
            "country breakdown. The headline uses the LOW estimate; high is "
            "carried for range display. feed_fish is a SUBSET of wild-caught "
            "fish (counts_in_total=false) — a footnote only, never added.",
        },
        "total_low": total_low,
        "total_high": total_high,
        "categories": categories,
        "feed_fish": feed_fish,
    }


def main():
    rows = []
    with open(SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if int(r["area_code"]) == CHINA_AGGREGATE:
                continue
            rows.append(r)

    # Reference year per species = TARGET_YEAR when present, else that
    # species' latest year (covers the two series that end in 2017).
    years_avail = defaultdict(set)
    for r in rows:
        years_avail[r["species"]].add(int(r["year"]))
    ref_year = {
        sp: (TARGET_YEAR if TARGET_YEAR in ys else max(ys))
        for sp, ys in years_avail.items()
    }

    world = defaultdict(float)                      # species -> count
    by_country = defaultdict(lambda: defaultdict(float))  # country -> species -> count
    country_code = {}
    for r in rows:
        sp = r["species"]
        if int(r["year"]) != ref_year[sp]:
            continue
        v = num(r["animals_killed"])
        if v <= 0:
            continue
        world[sp] += v
        by_country[r["country"]][sp] += v
        country_code[r["country"]] = int(r["area_code"])

    world_total = sum(world.values())

    species = sorted(world.keys(), key=lambda s: world[s], reverse=True)
    species_out = [
        {
            "id": sp,
            "name": DISPLAY.get(sp, sp.replace("_", " ").title()),
            "count": round(world[sp]),
            "year": ref_year[sp],
            "share": world[sp] / world_total,
            "group": "avian" if sp in AVIAN else "terrestrial",
        }
        for sp in species
    ]

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

    years_used = sorted({ref_year[sp] for sp in species})
    data = {
        "meta": {
            "source": "FAOSTAT — Crops and livestock products, "
            "Producing/Slaughtered animals",
            "source_url": "https://www.fao.org/faostat/en/#data/QCL",
            "reference_years": years_used,
            "primary_year": max(years_used),
            "generated": dt.date.today().isoformat(),
            "breaths_per_minute": 15,
            "note": "Land animals slaughtered for food worldwide. The FAO "
            "'China' aggregate is excluded to avoid double counting. Most "
            "series are "
            + str(max(years_used))
            + "; two minor series end in "
            + str(min(years_used))
            + ". Figures count individual animals, not biomass.",
        },
        "world_total": round(world_total),
        "species": species_out,
        "countries": countries_out,
    }

    # Aquatic animals — a structurally separate block (see build_sea). Added
    # last so the land keys above serialise byte-for-byte as before.
    data["sea"] = build_sea()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    sea = data["sea"]
    print(f"Wrote {OUT}")
    print(f"  world total : {round(world_total):,}  (land; sea excluded)")
    print(f"  species     : {len(species_out)}")
    print(f"  countries   : {len(countries_out)}")
    print(f"  ref years   : {years_used}")
    print(f"  sea cats    : {len(sea['categories'])} counted + feed_fish (subset, excluded)")
    print(f"  sea low     : {sea['total_low']:,}  (headline basis)")
    print(f"  sea high    : {sea['total_high']:,}")


if __name__ == "__main__":
    main()
