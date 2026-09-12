---
name: Industrial Intelligence System
colors:
  surface: '#fcf8f9'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf8f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f3'
  surface-container: '#f0eded'
  surface-container-high: '#ebe7e7'
  surface-container-highest: '#e5e2e2'
  on-surface: '#1c1b1c'
  on-surface-variant: '#45474b'
  inverse-surface: '#313031'
  inverse-on-surface: '#f3f0f0'
  outline: '#76777b'
  outline-variant: '#c6c6cb'
  surface-tint: '#5b5e66'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#181c22'
  on-primary-container: '#80848c'
  inverse-primary: '#c3c6cf'
  secondary: '#a04101'
  on-secondary: '#ffffff'
  secondary-container: '#ff8849'
  on-secondary-container: '#6b2900'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#231a11'
  on-tertiary-container: '#908175'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dfe2eb'
  primary-fixed-dim: '#c3c6cf'
  on-primary-fixed: '#181c22'
  on-primary-fixed-variant: '#43474e'
  secondary-fixed: '#ffdbcc'
  secondary-fixed-dim: '#ffb693'
  on-secondary-fixed: '#351000'
  on-secondary-fixed-variant: '#7a3000'
  tertiary-fixed: '#f2dfd1'
  tertiary-fixed-dim: '#d5c3b6'
  on-tertiary-fixed: '#231a11'
  on-tertiary-fixed-variant: '#51443a'
  background: '#fcf8f9'
  on-background: '#1c1b1c'
  surface-variant: '#e5e2e2'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono:
    fontFamily: IBM Plex Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
  container-max: 1440px
---

## Brand & Style

The design system is engineered for high-stakes industrial environments where precision, reliability, and clarity are paramount. It adopts a **Premium Industrial SaaS** aesthetic, blending the robust utility of a control room with the sophisticated minimalism of modern enterprise software.

The brand personality is authoritative yet approachable—think of a digital architect or a chief engineer. It evokes a sense of "Constructive Intelligence," where massive amounts of raw data are refined into actionable insights. 

**Visual Style: Corporate Modern with Industrial Accents**
- **Precision-focused:** 1px borders and structural alignment create a sense of engineered accuracy.
- **High Utility:** Intentional use of whitespace ensures that complex dashboards remain breathable and navigable.
- **Materiality:** While strictly flat, the use of a "burnt rust" accent and "charcoal navy" navigation creates a tactile connection to physical industrial materials like steel and oxidized iron.

## Colors

This color palette is designed for high legibility and long-duration monitor use. 

- **Primary (Charcoal Navy):** Used for global navigation and high-level hierarchy. It provides a "dark mode" anchor in a light-mode application, mimicking the heavy bezel of a physical control console.
- **Secondary (Burnt Rust):** An industrial-inspired amber used sparingly for primary actions, active states, and critical highlights.
- **Neutral Foundation:** The background (#F5F6F7) and surface (#FFFFFF) provide a subtle contrast to separate page structure from content cards.
- **Semantic Palette:** Standardized for industrial safety. Success represents operational stability, Warning indicates a threshold breach, and Error denotes equipment or system failure.

## Typography

The typography system prioritizes data scanning and information hierarchy.

- **Display & Headlines:** Use **Inter** (Tight-tracking) for a confident, geometric look. This is reserved for page titles and large-scale performance metrics.
- **Body:** **IBM Plex Sans** is used for all descriptive text. Its humanist qualities ensure legibility in dense data environments.
- **Technical Data:** **IBM Plex Mono** is strictly reserved for activity codes, serial numbers, coordinates, and raw log data. This prevents confusion between human-readable descriptions and system-generated identifiers.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** grid model.

- **Grid:** A 12-column grid system is used on desktop with 24px gutters. Content is housed in "Surfaces" (cards) that span specific column counts (e.g., 4 columns for sidebars, 8 for primary charts).
- **Rhythm:** An 8px spatial scale (with a 4px half-unit for tight components) governs all padding and margins.
- **Responsiveness:**
  - **Desktop (1440px+):** Fixed central container with wide margins.
  - **Tablet (768px - 1439px):** Fluid grid with 24px margins.
  - **Mobile (<768px):** 4-column fluid grid. The "Charcoal Navy" sidebar collapses into a bottom-anchored navigation bar or a condensed hamburger menu to maximize vertical space for data visualization.

## Elevation & Depth

This design system avoids heavy shadows to maintain a "technical drawing" feel. Depth is achieved through **Tonal Layering** and **Structural Outlines**.

- **Level 0 (Background):** #F5F6F7. The canvas for all content.
- **Level 1 (Surfaces):** #FFFFFF. White cards sit on the background, defined by a 1px border (#E2E4E9).
- **Level 2 (Interaction):** Active or hovered states utilize a very subtle, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)) to indicate clickability without breaking the minimal aesthetic.
- **Level 3 (Overlays):** Modals and dropdowns use a slightly darker 1px border and a medium shadow to separate them from the underlying data.

## Shapes

The shape language is **Soft (0.25rem)**. This maintains a disciplined, "engineered" look while removing the harshness of a purely sharp-edged interface. 

- **Standard Components:** Buttons, Input fields, and Chips use a 4px (0.25rem) radius.
- **Large Containers:** Dashboard cards and Modals use an 8px (0.5rem) radius.
- **Indicators:** Status pips and specific circular icons may use a full pill shape, but these are exceptions for semantic clarity.

## Components

- **Buttons:** 
  - *Primary:* Solid #C25A1E background with white text.
  - *Secondary:* 1px border of #12161C with matching text.
  - *Tertiary:* Ghost style, no border, #12161C text.
- **Input Fields:** 1px border (#D1D5DB). Focus state switches the border to #C25A1E with a 2px inner "industrial" glow.
- **Chips / Tags:** High-contrast for status. Use the semantic colors with a 10% opacity background and a 100% opacity text color (e.g., Success chip has light green background, dark green text).
- **Cards:** White background, 1px #E2E4E9 border. Headers within cards should have a subtle bottom divider.
- **Data Tables:** Zebra-striping is avoided. Instead, use thin 1px horizontal dividers. Header rows should use `label-caps` typography with a subtle gray background (#F9FAFB).
- **Navigation Sidebar:** #12161C background. Active links use the #C25A1E accent as a 4px vertical bar on the left edge.