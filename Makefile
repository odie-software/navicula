all: env dev

env:
	@echo "Setting up local development environment..."
	@echo "Installing dependencies..."
	@cd app/ && npx pnpm install
	
dev:
	@echo "Starting the dev server..."
	@docker compose -f compose.dev.yml up -d --force-recreate --build
	@echo "Navicula is up. Visit http://localhost:3000 to access it."