# Stage 1: Build the React app
FROM node:18-alpine as build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Set build-time environment variables
ENV REACT_APP_API_URL=http://192.168.10.18:8080
ENV REACT_APP_WS_URL=ws://192.168.10.18:8080
ENV REACT_APP_SOCKET_PATH=/socket.io/

# Build the app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built app from build stage
COPY --from=build-stage /app/build /usr/share/nginx/html

# Copy nginx configuration if needed
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]