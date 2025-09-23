FROM node:20-alpine
WORKDIR /app
# Copy only package files first for better layer caching
COPY apps/console/package.json apps/console/tsconfig.json /app/apps/console/
WORKDIR /app/apps/console
RUN npm install --no-audit --no-fund
# Copy the rest of the app
COPY apps/console /app/apps/console
EXPOSE 3000
CMD ["npm", "run", "dev"]
