.PHONY: run test docker-up docker-down

run: ## Start the dev server with reload.
	uvicorn app.main:app --reload

test: ## Run the test suite.
	python -m pytest -q

docker-up: ## Build and start the API in Docker.
	docker compose up --build

docker-down: ## Stop the Docker stack.
	docker compose down
