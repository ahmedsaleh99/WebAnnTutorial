FROM node:22-alpine

WORKDIR /app

RUN addgroup --gid 10001 app \
    && adduser --disabled-password --uid 10001 --ingroup app appuser

COPY --chown=appuser:app server.mjs ./server.mjs

USER appuser

EXPOSE 5173

CMD ["node", "server.mjs"]
