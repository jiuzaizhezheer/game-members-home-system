# Game Members Home System

基于 FastAPI 的「游戏会员之家」后端服务，提供业务 API、通知推送、消息与订单等能力。项目采用清晰的分层组织方式（路由 / schema / service / repo / entity / 数据库基础设施），并配套 Celery 进行异步/定时任务处理。

## 技术栈

- Web：FastAPI + Uvicorn
- 数据：PostgreSQL（业务主库）/ MongoDB（部分互动与内容数据）/ Redis（缓存、锁、计数等）
- 异步任务：Taskiq + RabbitMQ（原 Celery 已迁移，详见下文）
- 通知：WebSocket
- 依赖管理：PDM（Python >= 3.12）

## 依赖管理约定（重要）

新增/升级依赖一律使用 `pdm add`，以确保 `pyproject.toml` 与 `pdm.lock` 自动同步；不要手改依赖文件后再 install。

- 新增运行时依赖：`pdm add <pkg>`
- 新增开发依赖：`pdm add -G dev <pkg>`
- 升级依赖：`pdm add <pkg>@<version>`
- 只做安装/还原环境：`pdm install`

## 快速开始

### 1) 准备环境

- Python >= 3.12
- PDM >= 2.26.1
- Docker（推荐，用于拉起 PostgreSQL/MongoDB/Redis/RabbitMQ）

### 2) 配置环境变量

复制示例配置并按需填写：

```bash
cp .env.example .env
```

```powershell
Copy-Item .env.example .env
```

环境变量项见 [.env.example](file:///d:/Codes/graduation-project/game-members-home-system/.env.example)；其中 `SECRET_KEY` 必须设置为你自己的安全随机值。

### 3) 启动依赖服务（推荐）

```bash
make docker-up
```

如果本机没有 `make`，可直接使用：

```bash
docker compose up -d
```

默认端口：

- PostgreSQL：5432
- MongoDB：27017
- Redis：6379
- RabbitMQ：5672（管理台 15672）

### 4) 安装依赖并启动后端

```bash
make dev-install
make run
```

如果本机没有 `make`，可直接使用：

```bash
pdm install -G dev
pdm run uvicorn app.main:app --reload
```

服务默认启动在 `http://127.0.0.1:8000`，可访问：

- OpenAPI：`/docs`
- ReDoc：`/redoc`

## 常用命令

Makefile 已封装常用开发命令（见 [Makefile](file:///d:/Codes/graduation-project/game-members-home-system/Makefile)）：

- 安装依赖：`make install` / `make dev-install`
- 启动开发服务：`make run`
- 拉起/关闭依赖：`make docker-up` / `make docker-down`
- 一键质量检查：`make check`（format + lint + typecheck + test）

### 初始化管理员

```bash
pdm run python -m scripts.create_admin --username <username> --email <email> --password <password>
```

### Taskiq (异步/定时任务) - 推荐方案

```bash
# 启动 Worker（处理异步任务与延时任务）
pdm run taskiq worker app.tasks.tasks:broker --log-level INFO --workers 2

# 启动 Scheduler（处理周期性定时任务）
pdm run taskiq scheduler app.tasks.tasks:broker --log-level INFO
```

### Celery (旧方案，并行保留中)

```bash
pdm run celery -A app.tasks.celery_worker worker --loglevel=info -P solo
pdm run celery -A app.tasks.celery_worker beat --loglevel=info
```

### 数据库补丁脚本

```bash
pdm run python -m app.database.pgsql.table_structure_patch
```

## 目录结构（概览）

```
game-members-home-system/
├── app/
│   ├── main.py                     # FastAPI 应用入口
│   ├── api/                        # 路由聚合与依赖
│   │   ├── deps.py
│   │   ├── router.py
│   │   └── routers/                # 各业务路由
│   ├── schemas/                    # 请求/响应 DTO（Pydantic）
│   ├── services/                   # 业务编排层
│   ├── repo/                       # 数据访问层（对 DB/session 的封装）
│   ├── entity/                     # 实体定义（pgsql/mongodb）
│   ├── database/                   # pgsql/mongodb/redis 基础设施与初始化脚本
│   ├── core/                       # 配置、生命周期、WebSocket 管理等
│   ├── middleware/                 # 全局异常、安全、日志等中间件能力
│   ├── tasks/                      # Celery worker/beat
│   └── utils/                      # 通用工具
├── scripts/                        # 运维/初始化脚本
├── docker-compose.yml              # 本地依赖编排
├── .env.example                    # 环境变量示例
├── pyproject.toml                  # PDM 配置与依赖
└── Makefile                        # 常用命令封装
```
