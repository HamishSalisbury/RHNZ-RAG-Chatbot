# Build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build


FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Remove the default Nginx configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Add our configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

CMD ["sh", "-c", "echo PORT=$PORT; echo '--- CONFIG FILES ---'; ls -la /etc/nginx/conf.d/; echo '--- LISTEN PORTS ---'; nginx -T 2>&1 | grep -E 'listen[[:space:]]'; echo '--- END ---'; nginx -g 'daemon off;'"]