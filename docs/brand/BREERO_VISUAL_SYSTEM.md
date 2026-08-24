# BREERO Visual System — Approved Direction

Status: APPROVED BASELINE

This document is the source of truth for BREERO public-site visual design. All new public pages, components, images, illustrations, icons, marketing assets, and future portal-compatible brand work must follow these rules unless the owner explicitly approves a brand change.

## Brand feeling

BREERO must feel premium, friendly, modern, human, local, trustworthy, energetic, colorful, and clean. It must not look like generic SaaS, a crypto product, a cheap contractor template, a bank, or an over-designed AI gradient site.

Core message: **Home services, without the hassle.**

Primary CTA: **Book a service**
Secondary CTA: **Explore services**

## Approved palette

- Primary Blue: `#146EF5`
- Primary Blue Dark: `#0E52C6`
- Deep Navy: `#0B1F3A`
- Ink: `#10243E`
- Teal: `#18B7A0`
- Teal Dark: `#0F8C7A`
- Coral: `#FF6B6B`
- Sun Yellow: `#FFC857`
- Sky: `#EAF4FF`
- Mint: `#EAFBF7`
- Warm Cream: `#FFF8EC`
- Light Gray: `#F5F7FA`
- Mid Gray: `#66768A`
- Border: `#DCE4EC`
- White: `#FFFFFF`
- Success: `#198754`
- Warning: `#B66A00`
- Error: `#C93838`

### Color usage rules

Blue is reserved for primary action, links, active states, and major brand emphasis. Navy is used for headings, premium sections, footer, and high-trust surfaces. Teal is used for trust, positive service status, availability, and secondary positive emphasis. Coral and yellow are accent colors only and must not be used for long body text. Body copy should primarily use Ink `#10243E`.

Never invent page-specific colors. Every new color must map to a centralized token and preserve WCAG AA contrast.

### Approved gradients

- Blue: `linear-gradient(135deg, #146EF5 0%, #0E52C6 100%)`
- Blue/Teal accent: `linear-gradient(135deg, #146EF5 0%, #18B7A0 100%)`
- Warm section: `linear-gradient(135deg, #FFF8EC 0%, #FFFFFF 100%)`

Use gradients sparingly. Flat, clean surfaces remain the default.

## Logo direction

Approved direction: bold BREERO wordmark paired with a compact symbol combining a recognizable B with a home/door/service cue. The symbol should feel rounded, friendly, strong, and readable at favicon size. The visual family may use BREERO blue with teal/coral/yellow accent in the primary version, while white and dark variants stay simplified for contrast.

Required centralized assets:

- `apps/web/public/brand/breero-logo-primary.svg`
- `apps/web/public/brand/breero-logo-white.svg`
- `apps/web/public/brand/breero-logo-dark.svg`
- `apps/web/public/brand/breero-wordmark-primary.svg`
- `apps/web/public/brand/breero-wordmark-white.svg`
- `apps/web/public/brand/breero-wordmark-dark.svg`
- `apps/web/public/brand/breero-symbol-primary.svg`
- `apps/web/public/brand/breero-symbol-white.svg`
- `apps/web/public/brand/breero-symbol-dark.svg`
- `apps/web/public/brand/breero-favicon.svg`
- `apps/web/public/brand/favicon.ico`
- `apps/web/public/brand/apple-touch-icon.png`
- `apps/web/public/brand/icon-192.png`
- `apps/web/public/brand/icon-512.png`
- `apps/web/public/brand/og-default.png`

All application usage must route through brand components such as `Logo.tsx`, `BrandMark.tsx`, and `Wordmark.tsx`. Never paste duplicate inline logo SVGs into pages.

## Typography

Preferred: Manrope for the complete site unless a measured implementation benefit requires Inter for body/UI. Use Next.js font optimization.

Desktop targets:
- Hero H1: 56–72px
- Page H1: 48–56px
- H2: 36–44px
- H3: 24–30px
- Body Large: 18–20px
- Body: 16–18px
- Small: 14px

Mobile targets:
- Hero: 38–46px
- Page H1: 36–42px
- H2: 28–34px
- H3: 22–26px

Marketing copy must never become tiny.

## Shape, spacing, and depth

Use an 8px-based spacing system. Typical section spacing: 72–120px desktop and 48–72px mobile.

Radius tokens:
- Small: 8px
- Medium: 14px
- Large: 20px
- XL: 28px
- Pill: 9999px

Hero and major imagery may use 24–32px radii.

Shadows must be soft and premium. Avoid heavy black shadows. Cards may have subtle lift on hover, but motion must remain restrained.

## Image color-code rule

Every BREERO marketing image must visually belong to the same brand family.

Required photographic treatment:
- bright natural daylight
- clean white balance
- warm, realistic skin tones
- attainable European residential environments
- professional but non-staged expressions
- clean workwear
- realistic tools and environments
- subtle BREERO blue somewhere in clothing, tools, UI overlay, vehicle detail, prop, or environment when natural
- teal/coral/yellow may appear only as controlled secondary accents
- avoid neon, dark cinematic grading, heavy orange/teal grading, desaturated gray stock photography, oversaturated HDR, luxury-mansion imagery, fake AI-looking skin, excessive blur, or unrelated brand colors

### Visual balance target

A page should generally read as:
- 55–70% neutral/white/cream/sky/mint surfaces
- 15–25% navy/ink typography and dark trust surfaces
- 8–15% blue primary brand action
- 3–8% teal positive accents
- <=5% coral/yellow friendly accents

This is a visual guideline, not a literal pixel-analysis requirement.

### Image overlays

If text overlays photography, use a controlled navy or neutral gradient/scrim only when needed for accessible contrast. Do not place long text directly over visually busy images.

## Required image architecture

All images are replaceable through Git without component changes. Components consume a centralized manifest; no scattered hardcoded paths.

Runtime roots:

`apps/web/public/images/`

Subdirectories:
- `hero/`
- `services/`
- `lifestyle/`
- `trust/`
- `how-it-works/`
- `locations/`
- `partners/`
- `about/`
- `blog/`
- `campaigns/`
- `illustrations/`
- `placeholders/`

Core marketing set:

Hero:
1. `hero/home-hero.webp`
2. `hero/services-hero.webp`
3. `hero/booking-hero.webp`
4. `hero/trust-hero.webp`
5. `hero/partner-hero.webp`
6. `hero/about-hero.webp`

Services:
7. `services/plumbing.webp`
8. `services/electrical.webp`
9. `services/handyman.webp`
10. `services/heating.webp`
11. `services/cooling.webp`
12. `services/appliance-repair.webp`
13. `services/cleaning.webp`
14. `services/locksmith.webp`
15. `services/painting.webp`
16. `services/carpentry.webp`
17. `services/moving-help.webp`
18. `services/home-maintenance.webp`

Lifestyle:
19. `lifestyle/happy-homeowner.webp`
20. `lifestyle/technician-arrival.webp`
21. `lifestyle/technician-working.webp`
22. `lifestyle/family-home.webp`
23. `lifestyle/clean-modern-home.webp`
24. `lifestyle/booking-on-phone.webp`

Trust:
25. `trust/verified-professional.webp`
26. `trust/quality-check.webp`
27. `trust/support-team.webp`
28. `trust/service-guarantee.webp`

About/Partners:
29. `about/breero-team.webp`
30. `partners/partner-professional.webp`
31. `partners/service-van.webp`
32. `about/local-community.webp`

Original generation/export targets:
- Hero: 2400×1600
- Card/service: 1600×1200
- Square: 1200×1200
- Portrait: 1200×1600

Use WebP or AVIF. Use Next/Image with width/height, `sizes`, meaningful alt text, lazy loading, and `priority` only for above-fold hero media.

## Page image rules

Homepage: approximately 10–12 visible placements using one hero, 6–8 service images, one how-it-works/lifestyle image, one trust/professional image, and one partner/professional image. Reuse central service images instead of creating duplicates.

Each service page: normally 2–3 images — one hero/service image, one contextual lifestyle image, and optionally one detail image.

Other pages should use fewer, stronger images rather than filler stock photography.

## Page visual system

All public pages must feel related but not cloned. Shared header, footer, CTA hierarchy, tokens, cards, type, image grading, and trust patterns must remain consistent. Section composition may vary to prevent template fatigue.

Desktop hero preference: asymmetric 60/40 structure with strong copy/action, a meaningful service selector or utility, an expressive hero image, and at most 2–3 small floating trust/status elements.

Mobile: copy -> CTA -> image -> trust. No overlapping elements that break at 375px.

## Route families to prepare

Core:
`/`, `/services`, `/how-it-works`, `/why-breero`, `/pricing`, `/trust`, `/service-guarantee`, `/about`, `/contact`, `/help`, `/partners`, `/locations`

Services:
`/services/plumbing`, `/services/electrical`, `/services/handyman`, `/services/heating`, `/services/cooling`, `/services/appliance-repair`, `/services/cleaning`, `/services/locksmith`, `/services/painting`, `/services/carpentry`, `/services/moving-help`, `/services/home-maintenance`

Conversion/support:
`/book`, `/availability`, `/faq`, `/reviews`, `/emergency`, `/home-care`

Corporate/SEO:
`/careers`, `/press`, `/blog`, `/privacy`, `/terms`, `/cookies`

Dynamic architecture:
`/locations/[slug]`, approved campaign landing pages, approved blog detail pages, and service details only where they map legitimately to current/future catalog data.

## Non-negotiable truth rules

Do not invent customer counts, Trustpilot ratings, reviews, certifications, guarantees, pricing, serviceability, availability, insurance, partner earnings, or testimonials. Render metrics/testimonials only when verified/configured. Do not create fake customer, partner, ops, or admin portals.

## Responsive and accessibility rules

Prove layouts at 375, 430, 768, 1024, 1280, 1440, and 1920 widths. No horizontal overflow. Interactive targets should be at least 44×44px where practical. Use semantic landmarks, keyboard navigation, visible focus, proper labels, accessible menus/drawers/accordions/dialogs, meaningful alt text, color contrast, and reduced-motion support.

## Brand consistency acceptance

A page fails visual acceptance when it introduces arbitrary colors, off-brand image grading, a duplicate logo implementation, a new visual style that cannot be explained by tokens, fake metrics, generic filler stock, unreadable mobile copy, or excessive animation/gradient usage.

Every new page must reuse this system rather than invent a new one.