# fox-streak-marketplace

A [FoxStreak marketplace](https://github.com/julius-d/fox-streak/blob/main/docs/marketplace-api.md) —
a small, static, read-only catalog of question-set packs, hosted on GitHub
Pages at <https://julius-d.github.io/fox-streak-marketplace/>.

Add this source in FoxStreak with that URL to browse and import the packs
below.

## Layout

```
marketplace.json                        ← manifest (entry point)
packs/<pack-slug>/pack.json              ← pack listing
packs/<pack-slug>/sets/*.foxstreak.json  ← question sets
packs/<pack-slug>/images/*               ← images referenced by sets (imageType: "url")
schema/                                  ← JSON Schemas used to validate every file in CI
```

Every `url` in `marketplace.json`/`pack.json` is relative to the document it
was fetched from, so packs are free to use any internal layout — this one
groups each pack's listing, sets, and images under one folder.

## Adding or changing a pack

1. Create `packs/<slug>/pack.json` and its `sets/*.foxstreak.json` files
   (see [question-set-format.md](https://github.com/julius-d/fox-streak/blob/main/docs/question-set-format.md)
   for the set format, and
   [marketplace-api.md](https://github.com/julius-d/fox-streak/blob/main/docs/marketplace-api.md)
   for the manifest/pack-listing format).
2. Add an entry for it to `marketplace.json`.
3. Give the pack's own `id` and every set's/item's `id` a real UUID, and
   bump a set's `updatedAt` whenever its content changes — that's how
   FoxStreak detects updates.
4. Open a PR. CI validates every JSON file against the schemas in
   `schema/` before it can merge; pushing to `main` deploys to Pages.

## Current content

**Erdkunde 5. Klasse** — Germany's 9 land neighbours: which country is
which, and what their capitals are. Map images derived from
[OpenStreetMap](https://www.openstreetmap.org/copyright) boundary data
(© OpenStreetMap contributors, ODbL).
