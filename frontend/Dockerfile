FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html tsconfig*.json vite.config.ts ./
COPY src ./src
RUN npm run build

FROM node:22-alpine

WORKDIR /app

RUN addgroup --gid 10001 app \
    && adduser --disabled-password --uid 10001 --ingroup app appuser

COPY --chown=appuser:app server.mjs ./server.mjs
COPY --from=build --chown=appuser:app /app/dist ./dist

USER appuser

EXPOSE 5173

CMD ["node", "server.mjs"]
