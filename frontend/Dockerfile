# ---- stage 1: build the static bundle with node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG APP_VERSION=local
ENV VITE_APP_VERSION=$APP_VERSION
RUN npm run build

# ---- stage 2: serve it with nginx, running as the non-root nginx user ----
FROM nginxinc/nginx-unprivileged:1.30-alpine
# where nginx forwards /api. compose uses the "backend" service name,
# the helm chart overrides this with the release's backend service
ENV BACKEND_URL=http://backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
