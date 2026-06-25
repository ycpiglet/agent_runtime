# Agent Characters -- v3 (CC0 GrafxKid base, category sprites, LIVE + additive)

**Status:** SHIPPED -- wired into the live console Office Map as an **additive**
layer with a **v2 fallback** (v1 + v2 are preserved, never deleted).
**Tier:** `standard`.

> v1 (`../v1/`) and v2 (`../v2/`) are **preserved**. v3 is the next iteration the
> Owner picked: a cute pixel character on a **real CC0 base**, with roles grouped
> into a small set of CATEGORIES (not 34 unique bodies).

## What changed from v2 (Owner decisions)

- **Real CC0 base.** Built on the **GrafxKid "RPG character"** CC0 sprite the
  Owner chose from the quality spike (`../_compare-cc0/char4_rpg-assets.png`).
  Vendored under `base/` with provenance in `base/SOURCES.md` (CC0 1.0 --
  attribution NOT required; GrafxKid credited voluntarily).
- **8 categories, not 34 characters.** The 34 ORG-MODEL roles are grouped into
  **8 categories**. A category is distinguished by an **accessory overlay
  (hat/item)** + a **category token color** -- same body per category.

| Category | Token color | Accessory | Example roles |
| --- | --- | --- | --- |
| Engineering | blue | hard-hat | lead-engineer, worker-engineer |
| Design | teal | beret + brush | lead-designer, interface-designer, ux-evaluator, design-system-steward |
| Quality / Audit | red | magnifier + clipboard | qa, independent-auditor, risk-controller, release-integrity |
| Research | amber | binoculars | research-agent, business-analyst, growth-analyst, progress-scout |
| Leadership / Council | violet | crown + gavel | managing-partner, council, strategy-lead, planning-architect, portfolio-steward |
| Finance / Ops | yellow | coin + ledger | finance-controller, accounting-operator, asset-steward, revenue-analyst, sales-ops, operations-lead, support-operator |
| Marketing / Sales | green | megaphone + tag | marketing-lead, content-marketer, brand-steward, sales-lead, crm-operator, partnership-manager, customer-success-steward |
| Docs | gray | book | doc-steward, process-steward |

(Full role->category map is in `generate_sprites.py` `ROLE_CATEGORY` and the JS
twin `_V3_ROLE_CATEGORY`; all 34 canonical roles are covered, verified by tests.)

## What's here

| File | What it is |
| --- | --- |
| `base/` | The vendored CC0 GrafxKid "RPG character" base PNG + `SOURCES.md` (license/provenance). The shipped art is token-driven SVG; the PNG is the reference base. |
| `generate_sprites.py` | Deterministic generator. `python generate_sprites.py` re-emits the 8 category SVGs byte-identically. Edit the pixel grids / category maps here, never the SVGs by hand. |
| `<category>.svg` | One sprite per category (8 files). `var(--token, #hex)` fills so they render standalone on GitHub AND pick up the house theme when inlined. |

## How it ships to the live console

The on-disk SVGs are the **design catalog**. The console renders the SAME art via
a **JS twin** -- `patternV3Sprite(role, opts)` in
`src/agent_runtime/ui_design_assets.py` -- which emits **inline `fill=` per rect**
(so multiple sprites on one page never collide on shared CSS classes) and uses
**bare `var(--token)`** (no raw hex -> design-system gate stays green). The twin's
BASE / accessory / category maps are **identical** to this generator's, verified
cell-for-cell by `tests/test_v3_sprites.py::test_js_and_python_v3_grids_match`.

Integration is **additive**: `patternOfficeSprite(role, { assetVersion })` prefers
v3 and **gracefully falls back to the v2 chibi twin** (then to a base sprite), so
the slot is never empty and v1/v2 stay intact. `patternOfficeMapPlacement()`
injects the sprite + a glyph + word status badge (not color-only), an `aria-label`,
and a `role . status . task` hover tooltip. Office CSS keeps the `office-idle-bob`
keyframe (the GrafxKid frame we use is a single idle pose) with a
`@media (prefers-reduced-motion: reduce)` off-switch.

## Animation

The base sheet's frames are top-down poses; v3 renders a single front idle frame,
so idle motion stays the existing CSS `office-idle-bob` bob (respects
`prefers-reduced-motion`). No `steps()` sprite-strip animation is needed.

## Viewing the demo

`agents/project/ui/spike/office-map-demo-v3.html` is a self-contained populated
Office Map (~12 sample agents, all 8 categories). Regenerate with
`python agents/project/ui/spike/gen_office_demo_v3.py`, then open the HTML, or:

```bash
cd agents/project/ui/spike
python -m http.server 8903   # then open http://127.0.0.1:8903/office-map-demo-v3.html
```

## License

The base is **CC0 1.0** (GrafxKid; attribution not required) -- provenance in
`base/SOURCES.md` and `docs/design/agent-runtime/ASSET-REFERENCES.md`. The
accessory overlays + token recolors are **original** (repo license). Nothing in
the served JS bundle is a bundled raster.
