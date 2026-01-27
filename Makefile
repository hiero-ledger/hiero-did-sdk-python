.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry install
	@poetry run pre-commit install
	@poetry env activate

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running pyright"
	@poetry run pyright
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@poetry run deptry .

.PHONY: test
test:
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest --verbose --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: test-unit
test-unit:
	@echo "🚀 Testing code: Running pytest (unit tests only)"
	@HEDERA_DID_SDK_LOG_LEVEL="DEBUG" HEDERA_DID_SDK_LOG_FORMAT="%(asctime)s %(levelname)s: %(filename)s: %(message)s" poetry run pytest -s --verbose ./tests/unit

.PHONY: test-integration
test-integration:
	@echo "🚀 Testing code: Running pytest (integration tests only)"
	@HEDERA_DID_SDK_LOG_LEVEL="DEBUG" HEDERA_DID_SDK_LOG_FORMAT="%(asctime)s %(levelname)s: %(filename)s: %(message)s" poetry run pytest -s --verbose ./tests/integration

.PHONY: build
build: clean ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

.PHONY: clean
clean: ## clean build artifacts
ifeq ("$(OS)", "Windows_NT")
	@rmdir /s /q ./dist
else
	@rm -rf ./dist
endif

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@poetry run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@poetry run mkdocs serve

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
