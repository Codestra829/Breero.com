## Scope

Describe the user-visible or architectural change and the branch responsibility.

## Design-system compliance

- [ ] I used BREERO brand tokens and shared UI primitives.
- [ ] I did not add page-local colors, fonts, inline visual styles, or a parallel CSS system.
- [ ] CTA hierarchy is primary / outline / ghost / danger and uses shared button primitives.
- [ ] New public UI inherits the global SiteHeader and SiteFooter.
- [ ] Mobile, keyboard focus, and reduced-motion behavior were considered.
- [ ] I did not invent ratings, reviews, pricing, availability, guarantees, certifications, or capability claims.
- [ ] `pnpm test:design` passes on the complete comparison range.

## Validation

Record exact-head lint, typecheck, test, build, browser, accessibility, and design-guard evidence relevant to this change.

## Deployment

- [ ] This PR does not deploy or mutate the live server unless explicitly documented and approved in a dedicated release/deployment PR.
