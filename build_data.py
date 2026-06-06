#!/usr/bin/env python3
"""Build data.json for the slaughter clock from FAOSTAT data.

Source: animals_killed_by_species_country_year.csv (FAOSTAT, "Producing
Animals/Slaughtered" element). Each row is animals slaughtered for food of a
given species, in a country, in a year.

Method (kept deliberately conservative and reproducible):

  * The FAO area "China" (code 351) is an aggregate of China mainland,
    Hong Kong, Macao and Taiwan, all of which are also present as their own
    rows. We DROP code 351 so nothing is counted twice.
  * For each species we use its most recent year that has any data anywhere
    in the world (2024 for almost everything; 2017 for the two negligible
    "game" / "other mammals" series). This is the latest full picture FAO
    publishes.
  * A country's figure for a species is its value in that same reference
    year (absent = 0). Country figures therefore sum exactly to the world
    total.
"""
import csv
import json
import datetime as dt
from collections import defaultdict

SRC = "animals_killed_by_species_country_year.csv"
OUT = "data.json"
CHINA_AGGREGATE = 351  # drop: equals mainland + HK + Macao + Taiwan

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


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def main():
    rows = []
    with open(SRC, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if int(r["area_code"]) == CHINA_AGGREGATE:
                continue
            rows.append(r)

    # Reference year per species = latest year with any data.
    ref_year = defaultdict(int)
    for r in rows:
        sp = r["species"]
        ref_year[sp] = max(ref_year[sp], int(r["year"]))

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

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {OUT}")
    print(f"  world total : {round(world_total):,}")
    print(f"  species     : {len(species_out)}")
    print(f"  countries   : {len(countries_out)}")
    print(f"  ref years   : {years_used}")


if __name__ == "__main__":
    main()
