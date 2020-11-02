FROM node:12.19.0-alpine3.12
MAINTAINER Li Meng Jun "lmjubuntu@gmail.com"

COPY . /app
WORKDIR /app
RUN cp src/config.sample.js src/config.js && npm run build
ENV NODE_ENV production

ENV HOST 0.0.0.0

ENTRYPOINT ["/app/node_modules/.bin/next", "start"]
