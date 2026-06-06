# animal-slaughter-toll — project instructions

A static GitHub Pages memorial that counts up, in real time, the land animals
slaughtered for food worldwide. See `README.md` for the data source and method.

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

Versioning started at **v1.0**.
