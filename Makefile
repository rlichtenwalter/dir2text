.PHONY: help install format lint typecheck security deps test check build publish clean

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

build: ## Build sdist and wheel into dist/
	rm -rf dist/
	uv build

publish: ## Publish version TAG to PyPI (TAG=X.Y.Z CONFIRM=yes required)
	@test -n "$(TAG)" || { \
	  echo "ERROR: TAG=X.Y.Z required. Usage: make publish TAG=X.Y.Z CONFIRM=yes"; \
	  exit 1; \
	}
	@test "$(CONFIRM)" = "yes" || { \
	  echo "ERROR: CONFIRM=yes required. Usage: make publish TAG=X.Y.Z CONFIRM=yes"; \
	  exit 1; \
	}
	@git rev-parse "v$(TAG)" >/dev/null 2>&1 || { \
	  echo "ERROR: git tag v$(TAG) not found"; \
	  exit 1; \
	}
	@# Clean up any leftovers from a prior failed run
	@git worktree remove --force .publish-worktree 2>/dev/null || true
	@git worktree prune
	@rm -rf dist/ .publish-worktree
	@# Build the tagged version in an isolated worktree so the current
	@# checkout is untouched. Belt and suspenders: re-verify the
	@# pyproject.toml version at the tag and the built wheel version
	@# both match TAG before we call uv publish.
	@set -e; \
	git worktree add --detach .publish-worktree "v$(TAG)"; \
	trap 'git worktree remove --force .publish-worktree 2>/dev/null; git worktree prune' EXIT; \
	tag_version=$$(grep '^version = ' .publish-worktree/pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/'); \
	if [ "$$tag_version" != "$(TAG)" ]; then \
	  echo "ERROR: pyproject.toml at v$(TAG) declares version=$$tag_version, expected $(TAG)"; \
	  exit 1; \
	fi; \
	(cd .publish-worktree && uv build --out-dir ../dist); \
	if ! ls dist/dir2text-$(TAG)-*.whl >/dev/null 2>&1 || ! ls dist/dir2text-$(TAG).tar.gz >/dev/null 2>&1; then \
	  echo "ERROR: built artifacts in dist/ do not match version $(TAG):"; \
	  ls -la dist/ || true; \
	  exit 1; \
	fi; \
	echo "Publishing dir2text $(TAG) to PyPI from dist/..."; \
	uv publish

clean: ## Clean build artifacts
	rm -rf .pytest_cache .ruff_cache __pycache__ dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
