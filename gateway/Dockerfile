FROM nginx:1.27-alpine

LABEL maintainer="OpenCode" \
      version="1.0.0"

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O - http://localhost/health || exit 1
