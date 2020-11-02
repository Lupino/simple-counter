FROM node:10.16.3-alpine
MAINTAINER Li Meng Jun "lmjubuntu@gmail.com"

COPY . /app
WORKDIR /app
RUN npm install --registry=http://registry.npm.taobao.org  && cp src/config.sample.js src/config.js && npm run build
ENV NODE_ENV production

ENV HOST 0.0.0.0

ENTRYPOINT ["node", "/app/app.js"]
