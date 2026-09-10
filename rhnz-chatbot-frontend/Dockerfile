# Build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf.template /etc/nginx/conf.d/default.conf

CMD ["sh", "-c", "sed -i \"s/\\${PORT}/$PORT/g\" /etc/nginx/conf.d/default.conf && echo PORT=$PORT && echo '--- LISTEN PORTS ---' && nginx -T 2>&1 | grep -E 'listen[[:space:]]' && echo '--- END ---' && nginx -g 'daemon off;'"]