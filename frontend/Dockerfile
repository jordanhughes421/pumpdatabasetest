FROM node:20-alpine as build

WORKDIR /app

# Copy package.json from the frontend directory
COPY frontend/package*.json ./
RUN npm install

# Copy the frontend source code
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
