# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9 AS dependencies
WORKDIR /app/services/admin-center
COPY --chown=node:node services/admin-center/package.json services/admin-center/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then \
      NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca npm ci --omit=dev --ignore-scripts; \
    else npm ci --omit=dev --ignore-scripts; fi

FROM node:24-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
ENV NODE_ENV=production ADMIN_BIND_HOST=0.0.0.0 PORT=8787 ADMIN_DATA_DIR=/var/lib/bantai-admin
WORKDIR /app/services/admin-center
COPY --chown=node:node --from=dependencies /app/services/admin-center/node_modules ./node_modules
COPY --chown=node:node services/admin-center/package.json ./
COPY --chown=node:node services/admin-center/src ./src
COPY --chown=node:node admin/center /app/admin/center
COPY --chown=node:node assets/images /app/assets/images
COPY --chown=node:node assets/css /app/assets/css
COPY --chown=node:node assets/style.css /app/assets/style.css
COPY --chown=node:node data/columns.json /app/data/columns.json
COPY --chown=node:node tools/university-database/tokyo/data/complete /app/tools/university-database/tokyo/data/complete
COPY --chown=node:node tools/university-database/kanagawa/data/complete /app/tools/university-database/kanagawa/data/complete
COPY --chown=node:node tools/university-database/saitama/data/complete /app/tools/university-database/saitama/data/complete
RUN install -d -o node -g node -m 0700 /var/lib/bantai-admin /var/backups/bantai-admin
USER node
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:8787/healthz').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node","src/server.js"]
