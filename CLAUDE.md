# animal-slaughter-toll — project instructions

## What it is

A static GitHub Pages memorial that counts up, in real time, the land animals
slaughtered for food worldwide. The tone is **somber — an inscription, not a
dashboard**; keep copy and styling restrained.

The site is **served from the repo root** by GitHub Pages. `index.html` is the
whole site (markup + CSS + JS in one file) and at runtime it `fetch`es one
file, `data.json`, also in the root. There is no server and no build step on
the serving path — what is committed in root is what ships.

The site is also an **installable, offline-capable PWA**. `manifest.webmanifest`
makes it installable; `sw.js` (a service worker, registered from `index.html`)
pre-caches the shell — `index.html`, `data.json`, the manifest and icons — and
serves it offline. The page and `data.json` are **network-first** (fresh when
online, cached copy when offline). Each launch is a **fresh navigation** that
reruns the inline script, so the *"since you opened this page"* counter still
resets on every reopen, online or off — keep it that way (don't persist the
open time).

The data pipeline is:

```
data/raw/animals_killed_by_species_country_year.csv
        → scripts/build_data.py
        → data.json   (repo root)
        → index.html  (fetches data.json)
```

`data.json` is committed, so the build only needs to run when the source CSV or
the build logic changes; re-commit the regenerated `data.json` when it does.

## Versioning & commit workflow (standing instruction)

The site displays a version number at the top of the page — in `index.html`,
`<span id="version">`.

For **every** change to this project, without being asked again:

1. Make the change.
2. **Bump the version.** Read the current `vMAJOR.MINOR` from `index.html` and
   add `0.1`. When the minor reaches `.9`, roll over to the next major:
   … `v1.8` → `v1.9` → `v2.0` → `v2.1` … The version shown on the page and the
   version in the commit must match.
3. **Commit and push to `main`.**

When the change touches anything the service worker caches (the page, styles,
JS, `data.json`, or the icons), also bump the **`VERSION`** constant in `sw.js`
to the same `vMAJOR.MINOR`, so installed/offline clients purge the old cache and
pick up the new shell. (Online visits already refresh the cached page and data,
but keeping `VERSION` in step is the guarantee for offline clients.)

Versioning started at **v1.0**.

## Repo layout

```
animal-slaughter-toll/
├── index.html            # the whole site (markup + CSS + JS)
├── data.json             # generated; fetched by index.html at runtime
├── manifest.webmanifest  # PWA manifest — makes the site installable
├── sw.js                 # service worker — offline pre-cache of the shell
├── favicon.svg, favicon-32.png, apple-touch-icon.png
├── icon-192.png, icon-512.png, icon-maskable-512.png   # PWA icons (from favicon.svg)
├── .nojekyll             # tells Pages to serve files verbatim
├── CLAUDE.md, README.md
├── SEA_METHODOLOGY.md    # sea-data sources, framing, guardrails (see below)
├── scripts/
│   ├── build_data.py            # data/raw/…csv → data.json
│   └── parse_clean_sheets.py    # fishcount sheets → config/sea_species_detail.csv
├── config/
│   ├── sea_summary.csv          # headline sea figures (low/high per category)
│   └── sea_species_detail.csv   # per-species sea detail
└── data/
    ├── README.md
    └── raw/
        ├── animals_killed_by_species_country_year.csv   # the only CSV the build reads
        └── reference/    # 13 FAO code-lookup tables (provenance only, unused by code)
```

Keep `index.html`, `data.json`, `manifest.webmanifest`, `sw.js`, the favicons,
the PWA icons, and `.nojekyll` in **root** — that is what Pages serves. The
service worker's scope is its own directory, so it must stay in root too.

## Land data: counting traps that must never regress

The published toll (~86B/year) is only credible because two FAOSTAT pitfalls are
handled. If a future rebuild of the source CSV reintroduces either, the headline
number silently blows up or collapses. Guard both:

1. **Co-product double-counting.** Each slaughtered animal shows up in FAOSTAT
   under several products — meat, fats, offal, hides/skins — often with
   *identical* head counts. Summing products counts the same animal 3–4×. Count
   **one primary "Producing/Slaughtered Animals" item per species**, never the
   sum of co-products.
2. **Mixed thousand-units.** Poultry and small stock (chickens, ducks, turkeys,
   geese, rabbits) are reported in **units of 1000 head**, while cattle, pigs,
   sheep, etc. are in single head. Each "thousand head" series must be
   **×1000**. Miss it and chickens — ~89% of the total — collapse by three
   orders of magnitude.

The current `data/raw/…csv` is already in single-head, one-item-per-species
form; `build_data.py` only drops the FAO "China" aggregate (area code 351, which
equals mainland + HK + Macao + Taiwan) and anchors years (below).

The published **86B is the auditable country-sum** (every figure traces to a
reporting country, FAO row-level estimates included); FAO's own **World aggregate
is higher (~104B)** for ordinary aggregation/imputation reasons — it gap-fills for
non-reporting countries at the aggregate level. Both are legitimate FAO, and we
**intentionally use the country-sum** so every number is individually verifiable.
This gap is expected — not a bug to re-investigate.

## Anchoring

Figures are anchored to the **latest complete year, 2023**. FAO's 2024 data is
still partial/under revision and is treated as incomplete. `build_data.py` uses
2023 for every series that has it; the two negligible series (`game`,
`mammals_other`) end in 2017 and fall back to their own latest year. The
counter projects the annual total at a constant per-second rate.

## Sea / aquatic animals (next feature — guardrails)

Aquatic animals are the largest group by number. The **data and methodology
have landed** (`SEA_METHODOLOGY.md`, `config/sea_summary.csv`,
`config/sea_species_detail.csv`, `scripts/parse_clean_sheets.py`); **wiring
them into the site is still pending** — `index.html` does not yet read them.
Source is fishcount.org.uk (tonnage ÷ mean weight, so every figure is a range).
Guardrails for that work:

- Methodology lives in **`SEA_METHODOLOGY.md`**; the figures the site uses come
  from **`config/sea_summary.csv`** (per-species detail in
  `sea_species_detail.csv`).
- The headline sea figure uses the **LOW** estimate (conservative by design).
- `feed_fish` (wild fish caught for fishmeal/oil) is a **subset** of wild-caught
  fish — it carries `counts_in_total = FALSE`; show it as a footnote, **never
  add it on top** or it double-counts.

## Verification anchors

After any data change, sanity-check against these. If they drift, something
regressed (see traps above):

- **Land:** ~**86 billion**/year (86,076,509,475), ≈ **2,728**/second,
  **chickens ≈ 89%** of the total.
- **Sea (when added):** floor of ~**1.58 trillion**/year.

## Conventions

- **Commit to `main`**, one logical fix per commit, **version bump on every
  change** (see above). Keep commits internally consistent.
- The site is **fully static** — no backend, no framework. `localStorage` is
  used **only for UI preferences** (counter mode + opened-at toggle, under key
  `astc.opts`); that is acceptable. Don't put data or state that the site
  depends on into `localStorage`.
- **CSV I/O:** source CSVs carry a UTF-8 BOM — read with `encoding="utf-8-sig"`.
  Any CSV the project *writes* (e.g. `config/sea_summary.csv`) should be emitted
  with a **UTF-8 BOM** for spreadsheet compatibility. `data.json` is plain
  UTF-8 JSON (no BOM).
- Any keyboard shortcuts are **Ctrl-based**, to avoid clobbering single-key
  browser/AT behavior.
