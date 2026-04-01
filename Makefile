.PHONY: help install format lint typecheck security deps test check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

format: ## Format code
	uv run ruff check --fix src tests
	uv run ruff format src tests

lint: ## Run linter
	uv run ruff check src tests

typecheck: ## Run type checker
	uv run pyright src

security: ## Run security scan with bandit
	uv run bandit -c pyproject.toml -r src/

deps: ## Check dependency hygiene with deptry
	uv run deptry .

test: ## Run tests
	uv run pytest

check: format lint typecheck security deps test ## Run all checks

clean: ## Clean build artifacts
	rm -rf .pytest_cache .ruff_cache __pycache__ dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
