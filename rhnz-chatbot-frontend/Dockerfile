# Build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build


# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

CMD ["sh", "-c", "echo '=== NGINX CONFIG ==='; nginx -T; echo '=== END CONFIG ==='; nginx -g 'daemon off;'"]