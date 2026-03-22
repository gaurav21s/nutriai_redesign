# Uncodixify Style Rules

Use this file when implementing or reviewing UI with `uncodixify-ui`. Apply the rules directly; do not treat them as inspiration.

## Core stance

- Prefer conventional layout and component structure over visual novelty.
- Preserve existing product language and IA when present.
- If a UI choice feels like a default AI-generated move, reject it and choose the plainer option.
- Keep colors calm. Let hierarchy come from spacing, contrast, and structure before effects.

## Standard defaults

- Sidebars: 240-260px fixed width, solid background, simple border-right, no floating shell
- Headers: plain h1/h2 hierarchy, no eyebrow labels, no gradient text, no uppercase microcopy
- Sections: 20-30px padding, clear grouping, no dashboard hero strips
- Navigation: simple links, subtle hover state, no transform animation, no decorative badges
- Buttons: solid fill or simple border, 8-10px radius max, no pill-first styling
- Cards/Panels: 8-12px radius max, subtle border, no floating effect, shadows under roughly `0 2px 8px rgba(0,0,0,0.1)`
- Forms/Inputs: labels above fields, solid borders, clear focus ring, no floating labels
- Tables: clean rows, subtle borders, left-aligned text, restrained hover
- Tabs: underline or border indicator, no pill bar
- Badges: small and functional only, 6-8px radius max
- Icons: simple 16-20px shapes, no decorative icon chips
- Typography: use the existing product font or a deliberate neutral sans-serif; avoid lazy default stacks unless the product already uses them; body text around 14-16px
- Spacing: use a consistent 4/8/12/16/24/32 scale
- Borders: simple 1px solid lines
- Motion: 100-200ms ease, color/opacity transitions only unless interaction demands more
- Containers: predictable grid/flex layout, centered max width around 1200-1400px when appropriate

## Hard bans

- oversized rounded corners
- repeated 20-32px radii across sidebar, cards, buttons, and panels
- floating detached sidebars
- glassmorphism, frosted panels, blur haze, decorative glows
- generic dark SaaS gradient backgrounds
- blue/cyan heavy palettes by default
- hero sections inside internal dashboards without a real product reason
- dashboard filler: KPI grids, fake charts, donut charts, quota bars, trend pills
- decorative right rails, schedule rails, workspace promo panels
- uppercase eyebrow labels or small section headers
- `small` headers used as design garnish
- decorative copy blocks that explain how clean the interface is
- team-focus / recent-activity style filler panels
- nav badges, live chips, or colored status dots without functional need
- pill-heavy tag systems
- mixed alignment logic that creates dead space
- dramatic box shadows
- transform hover effects such as link nudges
- fake-premium typography tricks
- overpadded layouts
- mobile layouts that collapse into a single long stack of padded cards

## Banned structures from prior failures

Avoid these recurring patterns:

- 248-280px sidebar with a branded block at the top and generic nav below
- full-width dashboard hero strip above the real content
- three-column KPI card grid as the first content block
- multiple nested panel variants (`panel`, `panel-2`, `rail-panel`, etc.) used only to create visual variety
- quota or usage sections with progress bars
- footer meta lines describing the demo rather than the product
- "focus" cards with a small label and a bold sentence inside

## Layout guidance by surface

### Internal tools

- Use a standard app shell only when navigation complexity justifies it.
- Put operational content first: filters, tables, forms, queues, logs, activity, detail panes.
- Let density come from good spacing and typography, not from tiny cards or gimmicks.

### Landing pages

- Use normal section sequencing: hero, proof, features, pricing/CTA, footer when needed.
- Avoid importing dashboard aesthetics into marketing.
- Do not decorate the page with blobs, glass cards, or fake product panels.

### Forms and settings

- Prefer one or two readable columns.
- Keep labels explicit and close to inputs.
- Group fields by task, not by visual decoration.

### Data tables

- Use plain toolbars with search, filters, bulk actions, and pagination.
- Keep status styling restrained; not every status needs a badge.
- Favor readable row rhythm and stable column alignment over visual chrome.

## Copy rules

- Use product language, not startup wallpaper copy.
- Do not add ornamental descriptors like "operational clarity," "live pulse," or "control room" unless the product truly uses them.
- Avoid explanatory side notes unless they add genuine domain context.

## Color direction

- Prefer muted neutrals, charcoals, graphites, warm creams, olives, browns, and restrained accent colors.
- Be skeptical of palettes that drift toward bright blue/cyan, especially in dark mode.
- If using a provided palette, mute it further if needed so the content remains primary.

Starting directions from the source brief:

- Dark: `#0f0f0f`, `#1a1a1a`, `#1c1c1e`, `#18181b`, `#27272a`
- Light: `#faf8f5`, `#f8f9fa`, `#fcfcfc`, `#f5f5f4`, `#ffffff`
- Useful accents: `#b45309`, `#d97706`, `#059669`, `#65a30d`, `#e11d48`

Use brighter blues only when the existing product brand requires them.

## Review checklist

- Does the layout match the product type without trying to impress?
- Are borders, spacing, and typography carrying hierarchy instead of effects?
- Have decorative panels, badges, glows, and filler charts been removed?
- Are section headers plain and specific?
- Does mobile preserve structure and scannability?
