# Premium public website acceptance

Recorded 2026-08-12 from `codex/premium-public-web-brand`. Final SHA is recorded in PR #24 after
the certification commit is published.

## Results

- Repository lint: PASS (4/4 packages).
- Repository typecheck: PASS (4/4 packages).
- Repository unit/component tests: PASS, 49 tests total; web 26.
- OpenAPI frontend contract check: PASS, 26 required paths and payment purposes.
- Production build: PASS, 68 static/dynamic outputs; public marketing first-load JS 111 kB.
- Marketing manifest: PASS, 32 assets, 68 validated internal links, 12 actionable button definitions,
  13 CTA definitions and 42 intended public routes across 50 static route files. No placeholder-portal links.
- Chromium/Firefox/WebKit complete booking, account, responsive, production-route, smoke and axe
  suite: PASS, 243/243.
- Widths: PASS at 375, 430, 768, 1024, 1280, 1440 and 1920; visual screenshots also at 375,
  768 and 1440.
- Axe: no serious/critical findings on home, services, plumbing detail, how it works, `/book`,
  booking, login, account, about, contact and partners in the final matrix.
- Image-path, internal-link and forbidden portal-link validation: PASS.
- Screenshot set: 51 files covering 17 acceptance routes at three widths; manually reviewed for
  hierarchy, crop, typography, CTA priority, navigation, legal identity and footer consistency.
- Production-build route audit with the explicit test adapter: PASS for all 42 intended public routes
  at all seven required widths, with zero horizontal overflows, failed routes or BREERO console/page
  errors. Two third-party Stripe frame requests were aborted during page teardown; no BREERO resource failed.
- Production build reports 102 kB shared first-load JS and 111 kB for marketing routes. These are
  build metrics, not staging Core Web Vitals.
- Representative local Lighthouse results (mobile simulation against the production build):
  home 61/100/79/100 with LCP 5.3 s and CLS 0.368; services 97/100/79/100 with LCP 2.6 s and
  CLS 0; plumbing 99/100/79/100 with LCP 2.1 s and CLS 0; booking 89/100/79/100 with LCP
  3.3 s and CLS 0.102. Scores are Performance/Accessibility/Best Practices/SEO and are not
  staging Core Web Vitals.

## Limitations

- Generated photos are drafts, not real BREERO staff/customer evidence. Final licensed or consented
  assets should replace the same filenames. The draft set is visually consistent but intentionally
  reuses a small number of compositions across the 32 manifest slots.
- Five marketing services map to the current booking catalog. Other service pages are informational
  and say availability is unconfirmed.
- The production API origin at `api.breero.com` remains unavailable from the certification host, so
  live booking cannot be represented as operational and the screenshot evidence uses the explicit
  browser test adapter.
- Local Lighthouse performance identifies follow-up work on homepage layout stability/LCP and the
  booking entry LCP/CLS; no score is represented as a production measurement.
- The certification host remains at 100% reported filesystem utilization despite gigabytes of
  available blocks, so capacity remains an operational risk outside this public-site branch.
- No city location page or campaign is published until operations/content approval.
- Legal copy is a structured draft requiring jurisdiction-specific legal approval.
- No customer, partner, operations or admin portal was created.
