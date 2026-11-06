# AGENTS.md

This file provides guidance when working with code in this repository.

## What this is

A [FoxStreak marketplace](https://github.com/julius-d/fox-streak/blob/main/docs/marketplace-api.md) — a small, static, read-only catalog of question-set packs, hosted on GitHub Pages at <https://julius-d.github.io/fox-streak-marketplace/>. There is no application code here: the repository *is* the data (JSON files + images) that the FoxStreak app consumes.

## Layout

```
marketplace.json                        ← manifest (entry point, lists packs)
packs/<pack-slug>/pack.json              ← pack listing (lists sets)
packs/<pack-slug>/sets/*.foxstreak.json  ← question sets (the actual quiz items)
packs/<pack-slug>/images/*               ← images referenced by sets (imageType: "url")
schema/                                  ← JSON Schemas used to validate every file in CI
scripts/cleanup_pr_data.py               ← PR-label-triggered cleanup (see below)
```

Every `url` field is **relative**, resolved against the document it was fetched from (manifest → pack listing → set file). This is also enforced by the schemas (`not: pattern "^([a-zA-Z][a-zA-Z0-9+.-]*:|//)"`), so a pack is free to use any internal layout, but URLs must never be absolute or protocol-relative.

Current packs (for context — check `marketplace.json` for the live list):
- **erdkunde-5-klasse** — Germany geography for 5th grade (neighbouring countries + capitals, rivers, mountain ranges).
- **erdkunde-allgemein** — general/not-grade-specific geography (currently: USA states, Berlin boroughs).
- **englisch-5-klasse**, **mathe-allgemein** — English and math vocab/drill sets.

## Validating changes

There's no build step. Validate every JSON file against its schema with `ajv-cli` (same command CI runs):

```shell
npx --yes ajv-cli@5 validate --spec=draft2020 --strict=false -s schema/marketplace.schema.json -d "marketplace.json"
npx --yes ajv-cli@5 validate --spec=draft2020 --strict=false -s schema/pack.schema.json -d "packs/**/pack.json"
npx --yes ajv-cli@5 validate --spec=draft2020 --strict=false -s schema/question-set.schema.json -d "packs/**/sets/*.foxstreak.json"
```

This is the authoritative check — if ajv is happy, the file is structurally correct. CI (`.github/workflows/deploy.yml`) runs exactly these three commands on every push/PR, then deploys `main` to GitHub Pages.

## Adding or changing a pack

1. Create `packs/<slug>/pack.json` and its `sets/*.foxstreak.json` files — see [question-set-format.md](https://github.com/julius-d/fox-streak/blob/main/docs/question-set-format.md) for the item format and [marketplace-api.md](https://github.com/julius-d/fox-streak/blob/main/docs/marketplace-api.md) for the manifest/pack-listing format. The schemas in `schema/` are the enforceable subset of both docs — some rules (e.g. phone normalization, date ranges, language-code pairing specifics) are documented but not fully checkable by JSON Schema; the schema files' `description` fields call these out explicitly.
2. Add an entry for the pack to `marketplace.json`.
3. Give the pack's `id` and every set's/item's `id` a real UUID (random v4 is fine — the schema only checks the 8-4-4-4-12 hex shape, not version/variant nibbles). Bump a set's `updatedAt` (an ISO date) whenever its content changes — that's how FoxStreak detects updates.
4. For `choice` items: `choices` must hold only the *wrong*-answer distractors — never include the correct `answer` in that array.
5. Images referenced via `imageType: "url"` must use the full `https://julius-d.github.io/fox-streak-marketplace/...` URL (not a relative path) since the set JSON is consumed outside this repo's own hosting context by the FoxStreak app. `imageType: "url"` is reserved for marketplace/user-added items — bundled seed sets in the upstream FoxStreak app itself use `emoji`/`base64` instead, but that distinction doesn't apply to this repo, which only ever produces `url` images.
6. When using images add `imageCopyright`.
7. When creating or updating sets, correct the `itemCount` in the coressponding `pack.json`.

## `scripts/cleanup_pr_data.py`

Triggered by `.github/workflows/cleanup.yml` when a PR is labeled `cleanup` (not run on every PR). For every `packs/*/sets/*.foxstreak.json` file changed vs. the PR's base, it: regenerates the set's and every item's `id` with fresh UUIDs, strips the correct `answer` out of `choices` if present there, registers/updates the set's entry in its `pack.json` (id/title/itemCount/updatedAt), and ensures the owning pack is listed in `marketplace.json`. It then commits and pushes the result back to the PR branch. This means hand-authored PRs don't need perfectly minted UUIDs or manually-synced listings — but pushing directly to `main` does, since that workflow only fires on PRs.
