# Premium public website acceptance

Recorded 2026-08-12 from `codex/premium-public-web-brand`, based on application candidate
`337e8e9ef47378643d221fb6c97d4ebdfe69e342`.

## Results

- Repository lint: PASS (4/4 packages).
- Repository typecheck: PASS (4/4 packages).
- Repository unit/component tests: PASS, 49 tests total; web 26.
- OpenAPI frontend contract check: PASS, 26 required paths and payment purposes.
- Production build: PASS, 63 static/dynamic outputs; public marketing first-load JS 111 kB.
- Marketing manifest: PASS, 32 assets, 60 validated internal links across 46 static routes, and no placeholder-portal links.
- Chromium/Firefox/WebKit complete booking, account, responsive, smoke and axe suite: PASS, 108/108.
- Widths: PASS at 375, 430, 768, 1024, 1280, 1440 and 1920; visual screenshots also at 375,
  768 and 1440.
- Axe: no serious/critical findings on home, services, plumbing detail, how it works, booking,
  login, account, about and contact in the final focused matrix.
- Image-path, internal-link and forbidden portal-link validation: PASS.
- Screenshot set: 30 files covering the 10 acceptance routes at three widths; manually reviewed for hierarchy, crop, typography, CTA priority, navigation and footer consistency.
- Production build reports 102 kB shared first-load JS and 111 kB for marketing routes. These are
  build metrics, not staging Core Web Vitals.

## Limitations

- Lighthouse was not installed in the accepted toolchain and was not downloaded onto the host at
  100% disk utilization. No Lighthouse score is claimed.
- Generated photos are drafts, not real BREERO staff/customer evidence. Final licensed or consented
  assets should replace the same filenames.
- Six marketing services map to the current booking catalog. Other service pages are informational
  and say availability is unconfirmed.
- No city location page or campaign is published until operations/content approval.
- Legal copy is a structured draft requiring jurisdiction-specific legal approval.
- No customer, partner, operations or admin portal was created.
