# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS dependencies
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@10.0.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json
COPY packages/types/package.json packages/types/package.json
COPY packages/ui/package.json packages/ui/package.json
RUN pnpm install --frozen-lockfile

FROM dependencies AS build
ARG NEXT_PUBLIC_APP_URL=https://breero.com
ARG NEXT_PUBLIC_API_BASE_URL=https://api.breero.com/api/v1
ARG NEXT_PUBLIC_DEPLOYMENT_ENV=production
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
ENV NODE_ENV=production \
    NEXT_PUBLIC_API_MODE=live \
    NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_DEPLOYMENT_ENV=${NEXT_PUBLIC_DEPLOYMENT_ENV} \
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY}
COPY . .
RUN case "$NEXT_PUBLIC_DEPLOYMENT_ENV" in \
      production) test "$NEXT_PUBLIC_APP_URL" = "https://breero.com" && test "$NEXT_PUBLIC_API_BASE_URL" = "https://api.breero.com/api/v1" ;; \
      staging) test "$NEXT_PUBLIC_APP_URL" = "https://staging.breero.com" && test "$NEXT_PUBLIC_API_BASE_URL" = "https://api-staging.breero.com/api/v1" ;; \
      *) exit 1 ;; \
    esac \
 && test "$NEXT_PUBLIC_API_MODE" = "live" \
 && pnpm --filter @breero/web build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production \
    NEXT_PUBLIC_API_MODE=live \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup --system --gid 1001 breero && adduser --system --uid 1001 --ingroup breero breero
WORKDIR /app
COPY --from=build --chown=breero:breero /workspace/apps/web/.next/standalone ./
COPY --from=build --chown=breero:breero /workspace/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=breero:breero /workspace/apps/web/public ./apps/web/public
USER breero
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "apps/web/server.js"]
