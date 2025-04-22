all: dev lint

dev:
	@echo "Setting up local development environment..."
	@echo "Installing dependencies..."
	@cd app/ && npx pnpm install
	@echo "Starting the dev server..."
	@docker compose -f compose.dev.yml build --no-cache
	@docker compose -f compose.dev.yml up -d --force-recreate
	@echo "Navicula is up. Visit http://localhost:3000 to access it."

lint:
	@echo "Running linter..."
	@cd app/ && npx pnpm lint:fix && npx pnpm format:fix
	@echo "Linting complete."