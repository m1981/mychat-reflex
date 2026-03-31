# Colors for help system
BLUE := \033[36m
YELLOW := \033[33m
GREEN := \033[32m
RESET := \033[0m

.DEFAULT_GOAL := help

##@ General
.PHONY: help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(BLUE)Usage:$(RESET)\n  make $(YELLOW)<target>$(RESET)\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(GREEN)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

.PHONY: test-cov
test-cov: ## Run UNIT tests with strict coverage (Fail under 80%, excludes UI and integration tests)
	@echo "$(GREEN)Running Unit Tests with Coverage Check...$(RESET)"
	uv run pytest -m "unit" \
		--cov=school_hub \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=80

.PHONY: test-cov-simple
test-cov-simple: ## Run UNIT tests with simple console coverage report (shows missing lines)
	@echo "$(GREEN)Running Unit Tests with Simple Coverage Report...$(RESET)"
	uv run pytest -m "unit" \
		--cov=school_hub \
		--cov-report=term-missing \
		--cov-fail-under=0

.PHONY: test-unit
test-unit: ## Run only unit tests (fast, no coverage)
	@echo "$(GREEN)Running Unit Tests...$(RESET)"
	uv run pytest -m "unit"

.PHONY: test-integration
test-integration: ## Run only integration tests
	@echo "$(GREEN)Running Integration Tests...$(RESET)"
	uv run pytest -m "integration"

.PHONY: test-ui
test-ui: ## Run only UI tests (requires Playwright)
	@echo "$(GREEN)Running UI Tests...$(RESET)"
	uv run pytest -m "ui"

.PHONY: test-all
test-all: ## Run all tests (unit + integration + ui)
	@echo "$(GREEN)Running All Tests...$(RESET)"
	uv run pytest


##@ Playwright Testing

.PHONY: playwright-gui
playwright-gui: ## Open Playwright Inspector GUI for interactive test debugging
	@echo "$(GREEN)Opening Playwright Inspector GUI...$(RESET)"
	PWDEBUG=1 uv run pytest -m "ui" -s --headed

.PHONY: playwright-codegen
playwright-codegen: ## Open Playwright codegen tool to record tests
	@echo "$(GREEN)Opening Playwright Codegen...$(RESET)"
	uv run playwright codegen http://localhost:3000

.PHONY: playwright-trace
playwright-trace: ## Run UI tests with trace recording (view with: playwright show-trace)
	@echo "$(GREEN)Running UI tests with trace recording...$(RESET)"
	uv run pytest -m "ui" --tracing on
