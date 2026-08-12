# Editing the website

- Change the logo by replacing matching files in `apps/web/public/brand/`; usage stays centralized in `Logo.tsx`.
- Replace a hero or service photo with a WebP of the same filename under `public/images/`.
- Edit brand, CTA, navigation, service and page copy under `apps/web/content/`.
- Change colors in `apps/web/app/brand.css` tokens.
- Add a service by extending `content/services.ts`; set `bookingServiceId` only when it maps to the real catalog.
- Add a location to `content/locations.ts` only after operations approves real serviceability, then add a typed route.
- Add a campaign content file under `content/campaigns/`; keep `published:false` until approved.
- Add a route with its own `app/<route>/page.tsx`; reuse marketing templates instead of a conditional router.
- Preview with `pnpm --filter @breero/web dev`; `/brand-preview` is available only outside production.
- Validate with `pnpm --filter @breero/web validate:marketing` before committing.
