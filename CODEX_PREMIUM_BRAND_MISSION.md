# CODEX MASTER MISSION — BREERO Premium Public Website Brand

Repository: `appolon1908-hue/Breero.com`
Branch: `codex/premium-public-web-brand`

## Authority and scope

Implement the complete BREERO public website visual system and page family using the approved brand direction. Work autonomously through implementation, validation, screenshots, documentation, and a draft PR. Do not self-merge. Do not touch production/staging infrastructure, payments, finance, backend domain logic, jobs, migrations, DNS, or Caddy except for a tiny frontend-required contract correction that is clearly documented.

Only `apps/web` is a real runnable frontend. Do not turn placeholder customer, partner, operations, or admin directories into fake applications.

The visual source of truth is `docs/brand/BREERO_VISUAL_SYSTEM.md`. Read it before changing any public-facing UI. Every page and asset must follow its palette, image treatment, typography, radius, spacing, accessibility, and truth rules.

## Approved color tokens

Create centralized CSS/design tokens and use them everywhere:

```text
--breero-blue: #146EF5
--breero-blue-dark: #0E52C6
--breero-navy: #0B1F3A
--breero-ink: #10243E
--breero-teal: #18B7A0
--breero-teal-dark: #0F8C7A
--breero-coral: #FF6B6B
--breero-yellow: #FFC857
--breero-sky: #EAF4FF
--breero-mint: #EAFBF7
--breero-cream: #FFF8EC
--breero-gray-light: #F5F7FA
--breero-gray-mid: #66768A
--breero-border: #DCE4EC
--breero-white: #FFFFFF
--breero-success: #198754
--breero-warning: #B66A00
--breero-error: #C93838
```

Do not scatter raw color literals through page JSX unless required by an SVG asset. If a new color is unavoidable, add it centrally, document its purpose, and ensure WCAG AA contrast.

## Logo system

Use the approved logo direction: bold BREERO wordmark plus a rounded compact B/home/door/service mark. The primary mark may use blue with teal/coral/yellow accent; dark and white variants remain simplified for legibility.

Create or prepare centrally:

```text
apps/web/public/brand/
  breero-logo-primary.svg
  breero-logo-white.svg
  breero-logo-dark.svg
  breero-wordmark-primary.svg
  breero-wordmark-white.svg
  breero-wordmark-dark.svg
  breero-symbol-primary.svg
  breero-symbol-white.svg
  breero-symbol-dark.svg
  breero-favicon.svg
  favicon.ico
  apple-touch-icon.png
  icon-192.png
  icon-512.png
  og-default.png
```

Create:

```text
apps/web/components/brand/Logo.tsx
apps/web/components/brand/BrandMark.tsx
apps/web/components/brand/Wordmark.tsx
```

All pages must use these components rather than inline copies.

## Typography

Prefer Manrope throughout with Next.js font optimization. Use a second body family only if there is a measurable implementation benefit. Enforce the size system documented in `BREERO_VISUAL_SYSTEM.md`; marketing body copy must remain readable on mobile.

## Image architecture and permanent color rule

Create/maintain:

```text
apps/web/public/images/
  hero/
  services/
  lifestyle/
  trust/
  how-it-works/
  locations/
  partners/
  about/
  blog/
  campaigns/
  illustrations/
  placeholders/
```

Create `apps/web/content/images.ts` as the canonical runtime manifest. No marketing component may hardcode arbitrary image paths.

Every image must preserve the BREERO image treatment: bright natural daylight, clean white balance, warm realistic skin, attainable residential environments, competent approachable professionals, clean workwear, real tools/environment, and a subtle BREERO-blue visual cue where natural. Teal/coral/yellow are secondary accents only. Reject dark cinematic, neon, gray/desaturated stock, luxury mansion, heavy HDR, fake AI skin, and unrelated-color visual directions.

If an image cannot meet the brand treatment, do not use it merely to fill space.

Prepare exactly these 32 core slots:

```text
/images/hero/home-hero.webp
/images/hero/services-hero.webp
/images/hero/booking-hero.webp
/images/hero/trust-hero.webp
/images/hero/partner-hero.webp
/images/hero/about-hero.webp
/images/services/plumbing.webp
/images/services/electrical.webp
/images/services/handyman.webp
/images/services/heating.webp
/images/services/cooling.webp
/images/services/appliance-repair.webp
/images/services/cleaning.webp
/images/services/locksmith.webp
/images/services/painting.webp
/images/services/carpentry.webp
/images/services/moving-help.webp
/images/services/home-maintenance.webp
/images/lifestyle/happy-homeowner.webp
/images/lifestyle/technician-arrival.webp
/images/lifestyle/technician-working.webp
/images/lifestyle/family-home.webp
/images/lifestyle/clean-modern-home.webp
/images/lifestyle/booking-on-phone.webp
/images/trust/verified-professional.webp
/images/trust/quality-check.webp
/images/trust/support-team.webp
/images/trust/service-guarantee.webp
/images/about/breero-team.webp
/images/partners/partner-professional.webp
/images/partners/service-van.webp
/images/about/local-community.webp
```

Use WebP or AVIF runtime assets, Next/Image, correct dimensions, `sizes`, meaningful alt, lazy loading, and `priority` only for the above-fold hero.

## Page family

Prepare polished routes/templates for:

```text
/
/services
/how-it-works
/why-breero
/pricing
/trust
/service-guarantee
/about
/contact
/help
/partners
/locations
/services/plumbing
/services/electrical
/services/handyman
/services/heating
/services/cooling
/services/appliance-repair
/services/cleaning
/services/locksmith
/services/painting
/services/carpentry
/services/moving-help
/services/home-maintenance
/book
/availability
/faq
/reviews
/emergency
/home-care
/careers
/press
/blog
/privacy
/terms
/cookies
/locations/[slug]
```

Do not create pointless routes merely to meet a count. Only expose functionality that actually works. Partner is informational only until onboarding exists.

## Homepage

Implement in this order:

1. navigation
2. premium asymmetric hero
3. service search/category area
4. trust strip
5. popular services
6. how it works
7. lifestyle image feature
8. why BREERO
9. verified testimonials only when real/configured
10. guarantee/trust section
11. supported locations
12. homeowner CTA
13. partner informational CTA
14. FAQ
15. final booking CTA
16. premium footer

Headline: `Home services, without the hassle.`
Subheadline: `Book trusted professionals for repairs, maintenance and everyday home services.`
Primary CTA: `Book a service`
Secondary CTA: `Explore services`

Hero must not become a generic empty text-left/photo-right template. Use depth, one meaningful large image, useful service discovery, and at most 2–3 small trust/status accents.

## Service pages

Every service page must use a consistent template while retaining meaningful content:

- breadcrumb
- hero
- service name and short promise
- primary and secondary CTA
- hero/service image
- trust bar
- common problems
- what is included
- how booking works
- pricing explanation without invented pricing
- service options only when supported
- why BREERO
- professional standards
- verified reviews only when available
- service-area CTA
- FAQ
- final CTA

Use 2–3 meaningful images per service page, generally reusing the central service/lifestyle inventory rather than generating duplicates.

## Content architecture

Separate content from layout.

Create/maintain:

```text
apps/web/content/
  brand.ts
  cta.ts
  navigation.ts
  footer.ts
  images.ts
  services.ts or services/*.ts
  locations.ts
  testimonials.ts
  faqs.ts
  pages/
  campaigns/
```

A content editor should be able to change copy, CTA labels, images, service descriptions, or location content without JSX surgery.

## Shared components

Create/standardize reusable marketing sections, including where useful:

```text
Hero
TrustBar
ServiceGrid
ServiceCard
HowItWorks
WhyBreero
TestimonialGrid
Stats
FAQ
CTASection
FeatureSplit
ImageFeature
LocationGrid
PartnerCTA
Guarantee
ProcessTimeline
ReviewSummary
BookingCTA
NewsletterCTA
```

Use one icon family, preferably Lucide or the existing project standard. Do not mix arbitrary SVG packs or emoji icons.

## Mobile and responsive requirements

Prove at: 375, 430, 768, 1024, 1280, 1440, 1920.

Mobile is not a compressed desktop. Prioritize service discovery, booking, readable cards, accessible navigation, and 44×44px practical tap targets. No horizontal overflow and no broken floating hero elements at 375px.

## Accessibility

Require semantic landmarks, skip navigation, keyboard menus, visible focus, labels, accessible drawers/accordions/dialogs, contrast, meaningful alt, and `prefers-reduced-motion`. Run axe against homepage, services, a service detail, how-it-works, booking entry, about, and contact.

## Truth and safety rules

Never fabricate:
- customer counts
- ratings
- reviews/testimonials
- certifications
- insurance promises
- pricing
- service availability
- serviceability areas
- partner earnings
- guarantees not backed by the business

Render stats/testimonials only when source/config marks them verified. No fake customer/partner/ops/admin portal links.

## SEO and public hygiene

Every public page gets a unique title, description, canonical, OpenGraph metadata, and structured headings. Use structured data only when accurate: Organization, WebSite, Service, FAQPage, BreadcrumbList. Never create fake review/rating schema.

Generate sitemap only from actual published routes. Production public pages may be indexed; staging must remain NOINDEX/NOFOLLOW.

## Git-friendly editing

Preserve these replacement boundaries:

```text
Logo      -> apps/web/public/brand/
Images    -> apps/web/public/images/
Colors    -> centralized tokens/CSS variables
Text      -> apps/web/content/
Layout    -> apps/web/app/[route]/page.tsx
Reusable  -> apps/web/components/marketing/
```

A designer replacing a file such as `apps/web/public/images/services/plumbing.webp` with another image of the same name must update every use automatically.

## Documentation to finish

Create or update:

```text
docs/brand/README.md
docs/brand/colors.md
docs/brand/typography.md
docs/brand/logo-guidelines.md
docs/brand/images.md
docs/brand/voice.md
docs/brand/cta-system.md
docs/brand/editing-the-website.md
docs/brand/page-inventory.md
docs/brand/asset-inventory.md
```

Document every image filename, route, section, aspect ratio, recommended dimensions, alt intent, and status.

## Validation

Run all available project checks:

```text
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm contract:check
```

Run Playwright in Chromium, Firefox, and WebKit where supported. Validate relevant widths. Add automated validation that every image referenced by the image manifest exists and every internal CTA points to a real route. Broken marketing images or internal links must fail CI.

Run representative Lighthouse checks and report Performance, Accessibility, Best Practices, and SEO without gaming the result.

## Screenshot acceptance

Produce visual review screenshots for:

```text
/
/services
one service detail
/how-it-works
/why-breero
/trust
/partners
/about
/contact
/book
```

At 375, 768, and 1440 widths.

Review spacing, crop, logo, headings, button hierarchy, contrast, card alignment, image quality, mobile navigation, footer, and CTA consistency.

## Git delivery

Stay on `codex/premium-public-web-brand`. Keep infrastructure changes out of this branch. Commit intentionally. Open or update a draft PR targeting the current accepted frontend/application base. Do not self-merge.

## Final report

Return exact:

1. starting SHA
2. final SHA
3. routes implemented
4. public page count
5. service page count
6. image slot count and filenames
7. logo outputs
8. palette and token locations
9. typography system
10. CTA system
11. homepage structure
12. service template
13. content tree
14. image manifest structure
15. logo replacement instructions
16. image replacement instructions
17. responsive results
18. accessibility/axe results
19. Playwright results
20. Lighthouse results
21. internal-link validation
22. image-path validation
23. screenshots produced
24. limitations/blockers
25. draft PR URL/number

Do not declare PASS unless the corresponding validation actually ran and passed. Stop only for a genuine external blocker; otherwise continue autonomously through the full mission.