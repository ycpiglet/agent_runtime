# Agent Characters — Draft v1 (preserved asset library)

**Status:** FIRST DRAFT for Owner review — *show-and-iterate*, **NOT a final merge**.
**Tier:** `experimental` (DESIGN-SYSTEM.md maturity model). **Not wired into the
live console** (`ui_console_assets.py`) yet — that happens only after the Owner
picks a direction.
**Backs:** `RFC-2026-06-23-character-design-exploration.md` (P1 decision gate) and
its parent `RFC-2026-06-23-visual-identity-and-agent-characters.md`.
**Precedent:** extends the AR-587 deterministic, self-hosted, token-driven avatar
approach (`patternAgentAvatar`) and honors the AR-588 non-color-only status rule.

> This is a **preserved** library — per Owner direction, never discard variants.
> New iterations should land as `../v2/`, `../v3/`, … so every explored direction
> stays viewable.

## What's here

| File | What it is |
| --- | --- |
| `preview.html` | Standalone interactive preview. Opens directly in a browser, **no build step, no network**. Shows all role sprites in a sample Office-Map grid with a working **hover/focus → info tooltip** (role + status + current task), plus the style variants side by side and a full role gallery. Includes a light/dark toggle. |
| `<role>.svg` | One original sprite per role (34 files). Pixel grid drawn as `<rect>` elements so they render on GitHub. |
| `_variant-A-chibi-lead-engineer.svg` | Style variant A of the sample role (standard chibi — the default look). |
| `_variant-B-bighead-lead-engineer.svg` | Style variant B (extra-cute 2-head proportion). |
| `_variant-C-softline-lead-engineer.svg` | Style variant C (soft pastel outline, 여성향 gentle palette). |
| `generate_sprites.py` | Deterministic generator. `python generate_sprites.py` re-emits every SVG byte-identically. Edit the pixel grids / role map here, never the SVGs by hand. |

### Viewing the preview

```bash
cd agents/project/assets/agent-characters/v1
python -m http.server 8901        # then open http://127.0.0.1:8901/preview.html
```

(`file://` works too in most browsers; a tiny server avoids cross-origin SVG quirks.)

## Aesthetic rationale

The Owner asked for small, cute, **아기자기** characters in the feel of classic
Game-Boy-era / early-Pokemon-style sprites — **as a style reference only**. These
sprites are **100% original pixel art** authored in `generate_sprites.py`; no
Pokemon/Mario/any-game IP, no scraped sprites, no external art pipeline. That
keeps us licensing-safe and consistent with the AR-587/588 self-hosted precedent.

Concrete style choices grounded in the research below:

- **Chunky pixels, limited palette.** A 16×16 logical art grid scaled to 128px;
  every fill comes from the house token palette (≤ ~12 logical colors per sprite).
- **Chibi proportions, large eyes, soft blush.** ~2.5-head figure, big dark eyes
  with a white highlight, a soft blush row — the readable "cute" cues.
- **Role read at a glance via prop + accent + silhouette.** Each role gets a small
  headgear/tool accessory (hard-hat, beret, crown, monocle, megaphone, …) plus its
  semantic accent color, so role is distinguishable even at office-map size.
- **Status is never color-only.** Presence/action is a glyph badge (●/◉/∥/!/·) with
  a text label in the tooltip, carrying the AR-588 accessibility rule into the
  characters. `<title>` is present for screen readers; agents are keyboard-focusable.
- **Gentle idle bob.** A slow 2.8s vertical bob (disabled under
  `prefers-reduced-motion`) — alive, not toy-like, fitting the "control room" house style.

### Token-driven + GitHub-viewable (the one non-obvious trick)

Each `<rect>` fill is `var(--token, #hexfallback)`. When a sprite is **inlined into
the console DOM**, the house CSS variables win (auto-theming, light/dark). When the
SVG is loaded **standalone or on GitHub** (via `<img>` or the GitHub renderer), the
page's CSS variables do **not** cascade in — so the inline **hex fallback** applies
and the sprite still renders correctly. (A bare `var(--x)` with no fallback resolves
to the *initial* fill = black in that context — which is exactly the bug this avoids.)
Accent fallbacks use the **light-theme** token hex values.

## Research references (UX grounding)

Female-oriented / younger-target cute sprite + RPG metadata-delivery patterns:

- **Cute / chibi pixel-art principles** — limited 8–16 color palette, chunky pixels,
  2–3-head chibi proportions, clean outlines for readability, large expressive eyes,
  role conveyed by hairstyle/headgear/accessory silhouette. (CapCut chibi guide;
  CraftPix chibi sprite sets; SLYNYRD pixel-art blog; Sprite-AI 2D pixel-art style guide.)
- **Female-oriented (여성향) aesthetic** — soft/pastel/light palettes conveying a
  gentle, delicate feel; modest, readable character designs (basis for Variant C).
  (나무위키 여성향 게임; Pastel Girl; KCI research on female-oriented character design.)
- **RPG hover-tooltip / status-delivery UX** — tooltips concise (1–2 lines), triggered
  on **hover and focus** (accessibility), positioned near the trigger without covering
  it; status icons reveal a description on hover; critical info first in the hierarchy.
  (UXPin "What is a tooltip"; ORK Framework Unity tooltip HUD; patternsgameprog
  strategy-game tooltips; uxdworld tooltip guidelines; Justinmind game-UI principles.)

These directly shaped: chibi proportions + soft blush (cute), the role-prop silhouette
system (readable role cue), the hover **and** keyboard-focus tooltip with role/status/task
hierarchy (RPG metadata delivery), and Variant C's pastel/soft-outline treatment.

## Role → sprite mapping

Roles are the canonical ids from `agents/project/ORG-MODEL.yml`. Accent colors map to
the same semantic tokens as `_AVATAR_ROLE_ACCENT_PY` (AR-587), so character identity is
consistent with the existing avatars.

| Role | Accent | Prop / accessory (silhouette cue) |
| --- | --- | --- |
| managing-partner | violet | crown + gavel (director / final call) |
| lead-engineer | primary (blue) | hard-hat + wrench |
| worker-engineer | primary (blue) | helmet + bolt |
| lead-designer | teal | beret + paintbrush |
| design-system-steward | teal | beret + ruler/grid |
| interface-designer | teal | beret + paintbrush |
| ux-evaluator | teal | magnifier + check |
| research-agent | amber | binoculars + flag (scout) |
| qa | success (green) | clipboard + green check |
| independent-auditor | danger (red) | monocle + clipboard |
| doc-steward | muted | book + quill |
| risk-controller | danger (red) | shield |
| release-integrity | success (green) | rocket (CI/CD) |
| finance-controller / accounting-operator / asset-steward / revenue-analyst | warning (amber) | coin / ledger |
| marketing-lead / content-marketer / growth-analyst | amber | megaphone |
| brand-steward | violet | megaphone |
| sales-lead / crm-operator / partnership-manager / sales-ops | success (green) | deal tag |
| operations-lead / support-operator | primary (blue) | headset |
| customer-success-steward | teal | headset |
| process-steward | muted | headset |
| strategy-lead / planning-architect / portfolio-steward | violet | compass + map |
| business-analyst | primary (blue) | compass |
| council (diversity-council) | violet | crown + group (multi-perspective) |

Some roles in the same team/discipline intentionally share a prop family (e.g. the
four finance roles share the coin) and are separated primarily by accent + callsign;
if the Owner wants every role uniquely propped, that is a cheap v2 follow-up.

## Status model (mirrors the office-map payload)

| Status | Glyph | Meaning | maps to office-map field |
| --- | --- | --- | --- |
| working | ● | actively working | `presence` + `action_label` |
| reviewing | ◉ | reviewing / auditing | " |
| waiting | ∥ | waiting / queued | " |
| blocked | ! | blocked | " |
| offline | · | idle / offline | " |

## Open style choices for the Owner

1. **Which variant?** A (standard chibi — *recommended* default), B (bighead, maximally
   cute), or C (soft pastel outline, gentlest 여성향 read). The full role set is currently
   drawn in the **A** treatment; the chosen variant would be applied across all roles.
2. **How overtly "cute"?** These are tasteful operator-console chibis (on-message with the
   "control room, not toy" DESIGN.md identity), not loud mascots. Push cuter (bigger eyes,
   more blush, rounder) or pull more restrained?
3. **Per-role uniqueness vs. team families.** Keep shared prop families (cheaper, calmer) or
   give every one of the 34 roles a unique prop (more work, busier)?
4. **Office Map vs. d3-force agent map.** The RFC's open question: keep the Office Map as
   the expressive character surface, or fold characters into the already-shipped live agent
   map (one presence surface instead of two)?

## What this draft does NOT do (by design)

- No changes to `src/`, `reviews/`, or the live console — additive assets + this doc only.
- No promotion to `stable`, no new vendor/CDN dependency, no token-layer changes.
- No auto-merge — the PR is **held for Owner review**.
