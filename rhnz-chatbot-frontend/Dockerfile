FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf.template /etc/nginx/templates/default.conf.template

CMD ["sh", "-c", "echo PORT=$PORT; nginx -T 2>&1 | grep -E 'listen[[:space:]]'; nginx -g 'daemon off;'"]