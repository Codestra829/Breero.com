# BREERO Enterprise Design System

Status: **binding frontend governance**

This layer keeps BREERO's approved identity and applies the disciplined visual behavior associated with high-end aerospace and Fortune 500 sites: restrained motion, high contrast, deliberate spacing, precise geometry, strong typography, and one CTA hierarchy. It does **not** copy SpaceX, Starlink, or any third-party logo, asset, font, page composition, or proprietary artwork.

## Brand authority

The existing BREERO visual authority remains canonical:

- Primary blue: `#146EF5`
- Primary blue dark: `#0E52C6`
- Deep navy: `#0B1F3A`
- Ink: `#10243E`
- Teal: `#18B7A0`
- Coral: `#FF6B6B`
- Sun yellow: `#FFC857`
- White and approved neutral surfaces from `docs/brand/BREERO_VISUAL_SYSTEM.md`

The enterprise layer uses navy/white as the high-trust shell and BREERO blue for primary actions. Accent colors remain secondary. Codestra yellow is **not** BREERO's primary CTA color.

## Typography

BREERO uses **Manrope first** through Next.js font optimization. It is the single display/body family for the enterprise shell.

Fallback stack:

`Manrope, "Helvetica Neue", "Segoe UI", Arial, sans-serif`

Rules:

- navigation and compact CTA labels may use uppercase with controlled tracking;
- headings use tight tracking and balanced wrapping;
- body copy remains sentence case;
- marketing copy is never below 14px;
- page code must not introduce another font family or external font request.

## CTA hierarchy

Use shared `.br-button` primitives only.

1. **Primary** — BREERO blue; one dominant action per decision surface.
2. **Outline** — transparent/neutral supporting action.
3. **Ghost** — low-priority navigation or utility.
4. **Danger** — destructive actions only.

Required interaction rules:

- minimum practical target: 44px;
- default enterprise button: 50px;
- compact CTA: 44px minimum;
- large CTA: 54px;
- small corporate radius, never decorative pills for ordinary CTAs;
- keyboard-visible focus and reduced-motion support.

## Header

The global header is the application shell authority:

- 76px desktop / 70px mobile;
- dark navy high-trust shell;
- BREERO logo left;
- centered desktop navigation where space allows;
- account + primary CTA right;
- accessible mobile navigation;
- no page-local replacement headers.

## Footer

The global footer contains:

- final conversion section;
- BREERO positioning and legal identity;
- services, company, support, privacy/communications, and professional navigation;
- legal/privacy/accessibility links;
- no fake metrics, reviews, service availability, or guarantees.

## Layout and spacing

Use the existing container and an 8px-derived spacing rhythm.

- major sections: approximately 72–120px desktop and 48–72px mobile;
- one primary content axis per section;
- prefer asymmetry and whitespace over dense card walls;
- cards use the shared radius/border system;
- avoid heavy black shadows and excessive gradients;
- animation must be functional, restrained, and removable through reduced-motion.

## Page inheritance

`RootLayout -> AppShell -> SiteHeader + main + SiteFooter` is the required shell. New public pages automatically inherit the same header, footer, typography, focus rules, CTA primitives, and enterprise layer. Page-local parallel shells are prohibited.

## Design drift guard

Run:

```bash
pnpm test:design
```

The guard checks changed code and fails on newly introduced design drift including:

- literal HEX/RGB/HSL colors outside approved token/style authorities;
- inline visual styles;
- page/component font-family declarations;
- new CSS systems outside approved central style files;
- arbitrary Tailwind-style values and palette utilities;
- decorative full-pill geometry in ordinary page/component changes;
- root layout losing the enterprise layer;
- AppShell losing the shared header/footer;
- header losing the shared BREERO logo;
- required governance files disappearing.

The guard intentionally evaluates **added lines in the complete comparison range**, not just the final commit, so a violation cannot be hidden by a later unrelated commit.

## Exceptions

A genuine design-system change must be made in the approved central style authorities and reviewed as a design-system change. Do not bypass the guard in a page file. If a new token is required, add it centrally, document it, and use the token everywhere else.
