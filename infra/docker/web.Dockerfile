# syntax=docker/dockerfile:1.7
# CareerOS web (Next.js standalone). Build context: repository root.
#
#   deps   → node_modules from the lockfile (cached until it changes)
#   build  → `next build` with the API's internal address baked into the /api rewrite
#   run    → only the standalone server + static assets, as a non-root user
ARG NODE_VERSION=22

FROM node:${NODE_VERSION}-alpine AS deps
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund


FROM node:${NODE_VERSION}-alpine AS build
WORKDIR /web
# Rewrites (/api/* → FastAPI) are resolved at build time: the API's internal address
ARG API_URL=http://api:8000
ENV API_URL=${API_URL} NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /web/node_modules ./node_modules
COPY apps/web ./
RUN --mount=type=cache,target=/web/.next/cache npm run build


FROM node:${NODE_VERSION}-alpine AS run
WORKDIR /web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S web && adduser -S web -G web
COPY --from=build --chown=web:web /web/.next/standalone ./
COPY --from=build --chown=web:web /web/.next/static ./.next/static
COPY --from=build --chown=web:web /web/public ./public
USER web
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO /dev/null http://127.0.0.1:3000/sign-in || exit 1
CMD ["node", "server.js"]
