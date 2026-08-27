# BREERO Design System Migration

## Current state

BREERO already has centralized brand assets, Manrope, shared UI primitives, a global AppShell, SiteHeader, SiteFooter, responsive public pages, and an approved visual-system document. The enterprise layer strengthens those foundations rather than replacing them.

## Migration rule

Do not perform a risky one-shot rewrite of every existing page. Existing accepted CSS may remain until the page is touched for product work. New or materially edited UI must follow `docs/design-system.md`.

## Order

1. Keep the global shell and enterprise layer stable.
2. Route all new CTA work through shared `.br-button` variants.
3. Move new colors into central tokens instead of page CSS.
4. Remove page-local typography declarations when a page is materially edited.
5. Replace decorative pill buttons with the corporate radius system except where pill geometry communicates status/tags.
6. Consolidate repeated layout patterns into `@breero/ui` or shared web components.
7. Preserve verified accessibility and responsive behavior during each migration.
8. Keep product/application routes truthful to runtime capabilities; visual polish must never imply an unavailable booking, payment, provider, messaging, or review capability.

## Acceptance for a migrated page

A page is complete when:

- it inherits the global header/footer;
- no new raw visual values bypass central tokens;
- CTA hierarchy is unambiguous;
- focus/keyboard behavior works;
- 375px mobile has no horizontal overflow;
- reduced-motion behavior is respected;
- no fabricated proof, metrics, ratings, availability, or guarantees appear;
- `pnpm test:design`, lint, typecheck, tests, and production build pass for the exact head.
