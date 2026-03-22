---
name: uncodixify-ui
description: Refactor or design frontend UI so it avoids generic AI-generated aesthetics and instead uses restrained, conventional, product-grade interface patterns. Use when Codex is building or restyling dashboards, admin panels, forms, tables, sidebars, settings pages, landing pages, or component systems that should feel human-designed, operationally clear, and visually calm rather than decorative, glossy, or "premium SaaS" by default.
---

# Uncodixify UI

## Overview

Design with the assumption that the default AI UI instinct is wrong. Prefer standard information architecture, plain components, calm color systems, and direct copy.

Use this skill to remove "Codex UI" patterns: floating shells, oversized radii, soft gradients, decorative copy, fake-premium dashboards, filler KPI grids, ornamental badges, and other shortcuts that make interfaces look machine-generated.

## Workflow

### 1. Start from the product type

Choose a normal layout before styling:

- Internal app: use a standard app shell only if the information architecture needs it. Prefer a fixed-width sidebar around 240-260px, simple top toolbar, and content area with clear sections.
- Landing page: use full-width sections in a predictable order. Do not import dashboard tropes into marketing surfaces.
- Settings or forms: use narrow readable columns, labels above controls, and obvious grouping.
- Data-heavy screens: let tables, filters, and summaries drive the layout. Do not invent decorative panels around them.

### 2. Strip out AI-default styling

Reject the first idea if it looks like a generic AI dashboard. In particular, remove:

- oversized rounding
- floating glass or detached shells
- blue-black gradient backgrounds
- eyebrow labels, small uppercase headers, and decorative subcopy
- metric-card grids as filler
- fake charts, donut charts, progress bars, and trend pills without a product reason
- glows, haze, heavy shadows, and transform-based hover motion
- status dots, nav badges, and tags that exist only for decoration

Use [style-rules.md](./references/style-rules.md) for the detailed banned patterns and component defaults.

### 3. Rebuild with normal components

Apply standard, boring-on-purpose primitives:

- headers: plain `h1`/`h2` hierarchy, no eyebrow text
- cards: 8-12px radius, subtle border, little or no shadow
- buttons: solid or outlined, 8-10px radius max, never pill-first
- inputs: labels above fields, simple border, visible focus ring
- tables: left-aligned, readable row spacing, restrained hover state
- tabs: underline or border indicator, not segmented pills
- modals/dropdowns: centered or anchored, straightforward, minimal animation
- typography: use the existing product font or a neutral sans-serif chosen deliberately, readable body size, no forced "premium" pairings or lazy default stacks
- spacing: consistent 4/8/12/16/24/32 scale
- motion: opacity/color changes over 100-200ms; avoid transforms unless functionally necessary

### 4. Use restrained color and contrast

Keep the palette calm. Prefer neutral, graphite, brown, olive, charcoal, cream, or off-white directions over the usual blue/cyan AI palette. If using dark mode, keep surfaces matte and contrast clear.

If the product already has brand colors, preserve them and reduce surrounding ornament rather than inventing a new theme.

### 5. Keep copy functional

Write interface copy that explains the product, not the design. Avoid ornamental phrases such as "operational clarity" or "one place to track what matters." Do not add section notes unless they convey real product information.

### 6. Review before finishing

Check the final UI against this list:

- Would a human product designer plausibly ship this without apologizing for the styling?
- Is the layout predictable for the page type?
- Are decorative elements doing real work?
- Are the copy, colors, and controls quieter than the content?
- On mobile, does the layout stay structured instead of collapsing into one long stack of padded cards?

## Reference

Read [style-rules.md](./references/style-rules.md) when you need the concrete banned patterns, approved component defaults, or the provided palette directions.
