# Base image for building the application
FROM node:20 AS builder

# Set the working directory
WORKDIR /app

# Copy package manager files from the 'app' subdirectory in the build context
COPY app/package.json ./
COPY app/pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies using the lockfile
RUN pnpm install

# Copy the rest of the application code from the 'app' subdirectory
COPY . .

# Build the Nuxt application
# Nuxt build command usually runs from the directory with package.json
RUN pnpm build

# Prune development dependencies
RUN pnpm prune --prod

# --- Production Stage ---

# Use a smaller base image for the final application
FROM node:20-alpine AS runner

# Set the working directory
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
# ENV APP_CONFIG_PATH=/app/config/config.json # If using dynamic config

# Copy built output and necessary node_modules from the builder stage
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/node_modules ./node_modules
# Copy config.yml instead of config.json
COPY --from=builder /app/config.yml ./config.yml
COPY --from=builder /app/package.json ./package.json

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application
CMD ["node", ".output/server/index.mjs"]
