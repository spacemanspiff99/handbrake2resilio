FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY ui-frontend/package.json ui-frontend/package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY ui-frontend/src ./src
COPY ui-frontend/public ./public

# Build with optional API URL arg (defaults to empty = use relative paths)
ARG REACT_APP_API_URL=""
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

# Production stage: nginx
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config
COPY ui-frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
