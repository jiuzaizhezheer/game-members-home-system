.PHONY: \
	help \
	install dev-install \
	format lint typecheck test check \
	run \
	makemigrations migrate \
	pre-commit ci clean

# ========================
# 基础配置
# ========================
APP_MODULE = app.main:app
PYTHON = pdm run
ALEMBIC = $(PYTHON) alembic

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
	$(PYTHON) ruff format .
	$(PYTHON) ruff check . --fix

lint: ## Lint code
	$(PYTHON) ruff check .

typecheck: ## Static type checking
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
# 数据库
# ========================
makemigrations: ## Create new database migration
	$(ALEMBIC) revision --autogenerate -m "Auto migration"

migrate: ## Apply database migrations
	$(ALEMBIC) upgrade head

# ========================
# 工程化
# ========================
pre-commit: ## Run pre-commit on all files
	$(PYTHON) pre-commit run --all-files || $(PYTHON) python -m pre_commit run --all-files

ci: install check ## CI pipeline entry

clean: ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
