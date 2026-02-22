.PHONY: \
	help \
	install dev-install \
	format lint typecheck test check \
	run \
	docker-up docker-down \
	makemigrations migrate \
	pre-commit ci clean

# ========================
# 基础配置
# ========================
APP_MODULE = app.main:app
PYTHON = pdm run

# ========================
# 帮助
# ========================
help:
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | \
		awk 'BEGIN {FS = ":.*?##"}; {printf "  %-18s %s\n", $$1, $$2}'
	@echo ""

# ========================
# 安装依赖
# ========================
install: ## Install production dependencies
	pdm install

dev-install: ## Install development dependencies
	pdm install -G dev

# ========================
# 代码质量
# ========================
format: ## Auto format code
	$(PYTHON) python -c "import ruff.__main__" || $(PYTHON) pip install ruff
	$(PYTHON) ruff format .
	$(PYTHON) ruff check . --fix

lint: ## Lint code
	$(PYTHON) python -c "import ruff.__main__" || $(PYTHON) pip install ruff
	$(PYTHON) ruff check .

typecheck: ## Static type checking
	$(PYTHON) python -c "import mypy" || $(PYTHON) pip install mypy
	$(PYTHON) mypy app

test: ## Run tests
	$(PYTHON) pytest

check: format lint typecheck test ## Run all checks

# ========================
# 运行
# ========================
run: ## Run development server
	$(PYTHON) uvicorn $(APP_MODULE) --reload

# ========================
# Docker
# ========================
docker-up: ## Start docker services
	docker compose up -d

docker-down: ## Stop docker services
	docker compose down

# ========================
# 工程化
# ========================
pre-commit: ## Run pre-commit on all files
	$(PYTHON) python -c "import pre_commit" || $(PYTHON) pip install pre-commit
	$(PYTHON) pre-commit run --all-files || $(PYTHON) python -m pre_commit run --all-files

ci: install check ## CI pipeline entry

clean: ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
