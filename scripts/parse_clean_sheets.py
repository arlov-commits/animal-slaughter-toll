"""
parse_clean_sheets.py  -- extract ONLY the clean, trustworthy fishcount sheets.

Outputs sea_species_detail.csv with per-species/per-class detail for your
class / size-tier / sentience groupings. This is a DETAIL/EXPLORATION layer,
NOT the source of headline totals (use sea_summary.csv for those).

WHY ONLY THESE SHEETS:
  - Wild-fish 'GEMWs' sheet: clean per-CLASS summary (ray-finned, sharks/rays,
    lampreys, hagfish, chimaeras, lobe-finned). NOTE: its numbers are a SUBSET
    (~half) of the true wild total, because species with specific (non-generic)
    mean weights live in the messy 12,000-row Sheet1. So treat GEMWs class
    numbers as ILLUSTRATIVE of distribution, not as the wild total.
  - 2020-2022 mollusc & crustacean files: clean per-species rows (verified to
    sum to fishcount's published 2022 figures). Trustworthy.

DELIBERATELY SKIPPED:
  - The 2017 farmed-fish/decapod files: booby-trapped with (a)-(e) lettered
    subtotal rows and stacked tables. Outdated anyway; use sea_summary.csv prose.
  - Wild-fish Sheet1: a 12k-row interactive country-selector, not a clean table.

Put the 5 xlsx in data/fishcount/ (or edit FOLDER). Run: python parse_clean_sheets.py
"""
import pandas as pd, os, re

FOLDER = "data/fishcount"
OUT = "sea_species_detail.csv"

SENTIENCE = {  # documented tiering (see SEA_METHODOLOGY.md)
    "bivalve": "open_question", "gastropod": "low_evidence",
    "decapod": "evidence_sentient", "finfish": "evidence_sentient",
    "cephalopod": "evidence_sentient",
}

def clean_num(v):
    if pd.isna(v): return None
    s = str(v).replace("\xa0","").replace(",","").strip()
    if s in ("","-"): return None
    if s.startswith("<"): return 0.5
    try: return float(s)
    except: return None

def size_tier(mean_g):
    if mean_g is None: return "unknown"
    if mean_g < 20: return "tiny"
    if mean_g < 200: return "small"
    if mean_g < 2000: return "medium"
    return "large"

rows = []

def do_wild_classes(path):
    g = pd.read_excel(path, sheet_name="GEMWs", header=12)
    g = g[[c for c in g.columns if isinstance(c, str)]]
    g = g.dropna(subset=["Class"])
    g = g[g["Class"].astype(str).str.contains("(", regex=False)]
    for _, r in g.iterrows():
        lo, hi = clean_num(r.get("Numbers Lower (millions)")), clean_num(r.get("Numbers Upper (millions)"))
        mw = clean_num(r.get("Mean weight (lower) g"))
        cls = str(r["Class"])
        rows.append({
            "source_file": "wild_fish_GEMWs", "level": "class",
            "name": cls, "scientific": cls, "class": cls.split(" (")[0],
            "fishery": "wild_capture", "year": "2007-2016",
            "mean_weight_g": mw, "size_tier": size_tier(mw),
            "sentience_tier": "finfish", "capacity": SENTIENCE["finfish"],
            "low": None if lo is None else lo*1e6, "high": None if hi is None else hi*1e6,
            "note": "SUBSET of wild total (generic-mean-weight species only); illustrative of class distribution",
        })

def do_aquaculture_species(path, group, sentience_default):
    df = pd.read_excel(path, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    sp_col = "Species (Scientific name)"
    df = df.dropna(subset=[sp_col])
    yr_col = df.columns[-1]
    for _, r in df.iterrows():
        lo, hi = clean_num(r.get("Numbers (lower)")), clean_num(r.get("Numbers (upper)"))
        mw = clean_num(r.get("EMW (lower) in g"))
        name = str(r[sp_col])
        # crude class guess for molluscs by keyword; refine later in groupings config
        st = sentience_default
        if group == "mollusc":
            low = name.lower()
            if any(k in low for k in ["mussel","oyster","clam","scallop","cockle","carpet shell","tagelus","ark","pen shell"]):
                st = "bivalve"
            elif any(k in low for k in ["snail","abalone","murex","turban","conch","whelk","gastropod"]):
                st = "gastropod"
            else:
                st = "mollusc_other"
        rows.append({
            "source_file": os.path.basename(path)[:24], "level": "species",
            "name": name, "scientific": name, "class": group,
            "fishery": "aquaculture", "year": str(r.get(yr_col)),
            "mean_weight_g": mw, "size_tier": size_tier(mw),
            "sentience_tier": st, "capacity": SENTIENCE.get(st, "open_question"),
            "low": None if lo is None else lo*1e6, "high": None if hi is None else hi*1e6,
            "note": "",
        })

def main():
    wild = os.path.join(FOLDER, "fishcount_estimated_wild_fish_2007-2016.xlsx")
    moll = os.path.join(FOLDER, "Estimated_farmed_mollusc_numbers_2020-2022.xlsx")
    crus = os.path.join(FOLDER, "Estimated_farmed_crustacean_numbers_2020-2022.xlsx")
    if os.path.exists(wild): do_wild_classes(wild); print("parsed wild GEMWs class sheet")
    if os.path.exists(moll): do_aquaculture_species(moll, "mollusc", "bivalve"); print("parsed molluscs")
    if os.path.exists(crus): do_aquaculture_species(crus, "decapod", "decapod"); print("parsed crustaceans")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nwrote {OUT}: {len(out)} rows")
    print("by level:", out["level"].value_counts().to_dict())
    print("by sentience_tier:", out["sentience_tier"].value_counts().to_dict())
    print("by size_tier:", out["size_tier"].value_counts().to_dict())

if __name__ == "__main__":
    main()
