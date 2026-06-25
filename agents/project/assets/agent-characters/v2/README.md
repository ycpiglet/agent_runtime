# Agent Characters -- v2 (LIVE on the Office Map)

**Status:** SHIPPED -- wired into the live console Office Map. **Tier:**
`standard` (DESIGN-SYSTEM.md maturity model).
**Backs:** `RFC-2026-06-23-character-design-exploration.md` (P1) and its parent
`RFC-2026-06-23-visual-identity-and-agent-characters.md`. Owner approved **Path A
(CC0 / original-generated chibi)**, tone **chibi**, placement **Office Map**.
**Precedent:** extends the AR-587 deterministic, self-hosted, token-driven avatar
approach (`patternAgentAvatar`) and honors the AR-588 non-color-only status rule.

> v1 (`../v1/`) is **preserved**, never discarded. v2 is the next iteration that
> the Owner picked + that now renders in the console.

## What changed from v1 (Owner feedback: "more color, fill the empty center")

v1's head/torso read as a pale, sparse blob -- the near-white panel tint filled
the face and the body was a small accent patch. v2 fixes that:

- **Filled, warm face** -- a dedicated skin tone (`--office-skin`) fills the
  whole head instead of the near-white panel, so the center is never empty.
- **Hair cap** (`--office-hair`) crowns every head with a saturated block.
- **Bigger, fully-coloured torso** -- the accent body spans more rows and carries
  a center collar + button highlights, so the chest is a solid color block.
- **Cheeks + mouth + eye-shine** keep the cute "아기자기" read; a one-sided skin
  shade adds gentle volume.

Result: ~110 painted cells per sprite vs ~80 in v1 -- visibly denser + more
colourful, with no hollow middle.

## What's here

| File | What it is |
| --- | --- |
| `generate_sprites.py` | Deterministic generator. `python generate_sprites.py` re-emits every catalog SVG byte-identically. Edit the pixel grids / role map here, never the SVGs by hand. |
| `<role>.svg` | One original chibi sprite per role (34 files). Pixel grid drawn as `<rect>` elements with `var(--token, #hex)` fills so they render standalone on GitHub AND pick up the house theme when inlined. |
| `preview.html` | Standalone interactive preview (no build, no network) -- the full role gallery in a sample Office-Map grid with the hover tooltip + light/dark toggle. |

## How it ships to the live console

The on-disk SVGs are the **design catalog**. The console renders the SAME chibi
via a **JS twin** -- `patternChibiSprite(role, opts)` in
`src/agent_runtime/ui_design_assets.py` -- so the served bundle stays
self-contained (no extra HTTP route) and is token-only (no raw hex, keeps the
design-system gate green). The JS twin's BASE / prop / role maps are **identical**
to this generator's, verified cell-for-cell by
`tests/test_chibi_sprites.py::test_js_and_python_chibi_grids_match`.

Integration points:

- `patternOfficeMapPlacement()` injects the sprite at the agent slot, plus a
  glyph + word status badge (not color-only), an `aria-label`, and a richer
  `role . status . task` hover tooltip.
- Office CSS adds a subtle idle-bob keyframe animation with a
  `@media (prefers-reduced-motion: reduce)` off-switch.

## Viewing the preview

```bash
cd agents/project/assets/agent-characters/v2
python -m http.server 8902        # then open http://127.0.0.1:8902/preview.html
```

## License

100% **original** pixel art authored in `generate_sprites.py` (no third-party IP;
Game-Boy / early-Pokemon-era chibi are *style references only*). Covered by the
repo license. No external asset is bundled here, so no CC0/attribution entry is
required in `docs/design/agent-runtime/ASSET-REFERENCES.md` beyond the existing
"original-generated" direction note.
