# Game Members Home System

这是一个基于 FastAPI 构建的游戏会员家庭系统，采用分层架构设计，具有清晰的代码组织结构。

## 项目结构

```
game-members-home-system/
├── .github/                                # GitHub 配置目录
│   └── workflows/                          # GitHub Actions 工作流配置
│       ├── ci.yml                          # CI 持续集成工作流
│       ├── dev-deploy.yml                  # 开发环境部署工作流
│       └── pr-check.yml                    # Pull Request 检查工作流
├── app/                                    # 主应用程序目录
│   ├── main.py                             # 程序入口文件，负责应用的初始化和装配
│   ├── api/                                # API 接口层，处理 HTTP 请求和响应
│   │   ├── __init__.py
│   │   ├── deps.py                         # 依赖项定义
│   │   ├── router.py                       # 路由聚合
│   │   └── routers/                        # 具体路由实现
│   ├── core/                               # 核心基础设施，提供配置、安全、日志等核心功能
│   │   ├── __init__.py
│   │   ├── config.py                       # 应用配置管理
│   │   ├── exceptions.py                   # 异常定义和处理
│   │   ├── lifespan.py                     # 应用生命周期管理
│   │   ├── logging.py                      # 日志配置
│   │   └── security.py                     # 安全相关功能（密码、JWT等）
│   ├── crud/                               # 数据库操作层，封装增删改查操作
│   │   ├── __init__.py
│   │   └── base.py                         # CRUD 基类
│   ├── database/                           # 数据库基础设施，提供连接和会话管理
│   │   ├── __init__.py
│   │   ├── base.py                         # 数据库基类定义
│   │   └── session.py                      # 数据库会话管理
│   ├── models/                             # ORM 模型，定义数据库表结构
│   ├── schemas/                            # Pydantic 模型，定义数据验证和序列化
│   │   ├── __init__.py
│   │   └── common.py                       # 通用数据模型
│   ├── services/                           # 业务逻辑层，实现核心业务逻辑
│   ├── tasks/                              # 后台任务，处理异步和定时任务
│   │   ├── __init__.py
│   │   └── celery_worker.py                # Celery 工作进程配置
│   ├── tests/                              # 测试，包含所有单元测试和集成测试
│   │   ├── __init__.py
│   │   ├── conftest.py                     # 测试配置
│   │   └── env_test                        # Python环境测试
│   └── utils/                              # 工具函数，提供通用工具方法
│       ├── __init__.py
│       └── time.py                         # 时间处理工具
├── .env                                    # 环境变量配置文件
├── .gitignore                              # Git 忽略文件配置
├── .pre-commit-config.yaml                 # Pre-commit 钩子配置
├── docker-compose.yml                      # Docker Compose 编排配置
├── Dockerfile                              # Docker 镜像构建文件
├── Makefile                                # 常用命令脚本
├── pdm.lock                                # PDM 锁定文件
├── pyproject.toml                          # 项目配置和依赖管理
└── README.md                               # 项目说明文档
```


uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
