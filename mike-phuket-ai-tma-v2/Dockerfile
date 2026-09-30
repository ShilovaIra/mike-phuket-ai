FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html styles.css profile.mjs catalog.mjs /usr/share/nginx/html/
COPY assets /usr/share/nginx/html/assets

EXPOSE 80
