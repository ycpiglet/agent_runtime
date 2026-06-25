# v3 Base Sprite — Source & License (CC0)

The v3 agent-character system is built on a **CC0 / Public-Domain** pixel-art base
that the Owner selected from the sprite-quality spike (`_compare-cc0/`).

## Chosen base

- **Saved filename:** `grafxkid-rpg-character_CC0.png` (full sheet)
  and `grafxkid-rpg-character_CC0_frame.png` (single representative front frame).
- **Original spike filename:** `char4_rpg-assets.png` (`_compare-cc0/`).
- **Title:** "RPG character sprites" (the GrafxKid "RPG character").
- **Source page:** https://opengameart.org/content/rpg-character-sprites
- **Direct download URL used:** https://opengameart.org/sites/default/files/RPG_assets.png
- **License:** **CC0 1.0 (Creative Commons Zero / Public Domain Dedication).**
- **Author / submitter:** **GrafxKid** (OpenGameArt.org).
- **Attribution required:** **No (CC0 — attribution NOT required).** Crediting GrafxKid
  is appreciated but optional. We credit them here voluntarily.
- **Dimensions:** 128 x 128 px, RGB PNG.
- **Type:** SHEET — top-down / RPG character sprites plus a few small props.
- **Verified:** CC0 status confirmed by reading the OpenGameArt.org asset page before
  download (recorded in `../_compare-cc0/SOURCES.md`, the spike's source ledger).
- **Downloaded:** 2026-06-25 (per the spike ledger).

## How v3 uses the base

The PNG above is **vendored here as the chosen CC0 reference base** (proportions,
palette feel, "cute RPG character" read). The shipped v3 sprite art is rendered
deterministically as **token-driven pixel SVG** by `../v3/generate_sprites.py`
(and its JS twin in `src/agent_runtime/ui_design_assets.py`), so the served bundle
stays self-hosted, hex-free, and theme-aware. Per-CATEGORY identity comes from an
**accessory overlay (hat/item) + a category token color** — NOT 34 distinct bodies.

Because the base is CC0, no attribution is legally required in the shipped product.
This file records the provenance anyway (good hygiene + `ASSET-REFERENCES.md` note).

## Sibling CC0 candidate (also GrafxKid, not chosen)

- `char3_classic-hero.png` — GrafxKid "Classic Hero / Mr. Man" (CC0). A side-view
  platformer hero; not chosen because the Owner picked the front-facing **RPG
  character** for the top-down Office Map read.
