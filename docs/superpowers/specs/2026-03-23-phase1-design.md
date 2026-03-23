# 齐家 · Phase 1 设计文档 — "能用"

**版本**：v1.0
**日期**：2026-03-23
**状态**：已确认

---

## 1. 目标

把家里的持仓录进去，看到总资产和盈亏。行情暂时手动输入。

**完成标准**：用户可以登录系统，手动添加持仓和交易记录，在首页看到总资产、持仓列表和资产配置饼图。Docker Compose 一键启动全部服务。

---

## 2. 架构

```
浏览器
  ↕ HTTP (REST API)
Next.js 14+ 前端 (TypeScript, shadcn/ui, Tailwind CSS)
  ↕ HTTP (REST API, /api/v1/*)
FastAPI 后端 (Python 3.11+)
  ↕ SQLAlchemy 2.0 (async) + Alembic
PostgreSQL 16
  ↕
Redis 7 (Session 存储)
  ↕
Docker Compose (nginx + next + fastapi + pg + redis)
```

前后端分离：Next.js 负责 UI 渲染，FastAPI 提供 REST API。前端通过 API 调用后端，后端通过 SQLAlchemy 访问数据库。

---

## 3. 技术选型

| 层次 | 选型 | 版本 |
|------|------|------|
| 前端框架 | Next.js | 14+ |
| 前端语言 | TypeScript | 5+ |
| UI 组件库 | shadcn/ui + Radix UI | latest |
| CSS | Tailwind CSS | 3+ |
| 图表 | Recharts | latest |
| 后端框架 | FastAPI | 0.110+ |
| Python | Python | 3.11+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库迁移 | Alembic | 1.13+ |
| 数据库 | PostgreSQL | 16 |
| 缓存 | Redis | 7 |
| 密码哈希 | bcrypt (passlib) | latest |
| 依赖管理 | pip + requirements.txt | — |
| 部署 | Docker Compose | v2 |

---

## 4. Phase 1 功能范围

### 4.1 用户登录

- 2~3 个预设用户账号（通过初始化脚本创建）
- 密码 bcrypt 哈希存储
- Session 存储在 Redis，7 天过期
- 登录/登出 API
- 前端登录页，未登录跳转登录

### 4.2 持仓 CRUD

- 添加持仓：标的代码、名称、资产类型、数量、成本价、账户（可选）
- 编辑持仓：修改数量、成本价等
- 删除持仓
- 手动更新最新价格（Phase 1 不接 AKShare）
- 资产类型：股票 / 基金 / 债券 / 现金 / 其他

### 4.3 交易记录

- 四种交易类型：买入 / 卖出 / 现金分红 / 红利再投资
- 交易自动更新持仓：
  - 买入：增加数量，移动加权平均更新成本价
  - 卖出：减少数量，成本价不变，计算本次盈亏
  - 现金分红：不影响持仓数量，记录现金流入
  - 红利再投资：增加数量，成本价摊薄
- 交易历史列表（按时间排序）

### 4.4 首页总览

- 总资产（总市值、总成本、总盈亏、总收益率）
- 持仓列表（名称、数量、市值、盈亏、占比）
- 资产配置饼图（按资产类型）
- 日涨跌暂不实现（需要行情数据，Phase 2）

### 4.5 操作日志

- 记录关键操作：添加/编辑/删除持仓、记录交易
- 记录操作人、操作类型、详情、时间

---

## 5. 数据库设计

### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| username | VARCHAR(50) UNIQUE | |
| password_hash | VARCHAR(255) | bcrypt |
| display_name | VARCHAR(100) | 显示名称 |
| created_at | TIMESTAMP | |

### holdings

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| symbol | VARCHAR(20) | 标的代码 |
| name | VARCHAR(100) | 标的名称 |
| asset_type | VARCHAR(20) | 股票/基金/债券/现金/其他 |
| quantity | DECIMAL(18,4) | 持有数量 |
| cost_price | DECIMAL(18,4) | 成本价 |
| latest_price | DECIMAL(18,4) | 最新价格（手动输入） |
| latest_price_updated_at | TIMESTAMP | 最新价格更新时间 |
| account | VARCHAR(100) | 来源账户（可选） |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### transactions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| holding_id | UUID (FK → holdings) | 关联持仓 |
| symbol | VARCHAR(20) | 标的代码（冗余，方便查询） |
| type | VARCHAR(20) | 买入/卖出/现金分红/红利再投资 |
| quantity | DECIMAL(18,4) | 数量 |
| price | DECIMAL(18,4) | 成交价 |
| fee | DECIMAL(18,4) | 手续费（可选） |
| realized_pnl | DECIMAL(18,4) | 本次实现盈亏（卖出时计算） |
| date | DATE | 交易日期 |
| user_id | UUID (FK → users) | 操作人 |
| created_at | TIMESTAMP | |

### sessions

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | VARCHAR(128) (PK) | |
| user_id | UUID (FK → users) | |
| created_at | TIMESTAMP | |
| expires_at | TIMESTAMP | |

### operation_logs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| action | VARCHAR(50) | 操作类型 |
| detail | TEXT | 操作详情 (JSON) |
| created_at | TIMESTAMP | |

---

## 6. API 设计

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录 |
| POST | /api/v1/auth/logout | 登出 |
| GET | /api/v1/auth/me | 获取当前用户信息 |

### 持仓

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/holdings | 持仓列表 |
| POST | /api/v1/holdings | 添加持仓 |
| PUT | /api/v1/holdings/{id} | 编辑持仓 |
| DELETE | /api/v1/holdings/{id} | 删除持仓 |
| PATCH | /api/v1/holdings/{id}/price | 手动更新最新价格 |

### 交易

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/transactions | 交易历史（支持按标的过滤） |
| POST | /api/v1/transactions | 记录交易（自动更新持仓） |

### 总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/dashboard/summary | 资产总览（总市值、盈亏等） |
| GET | /api/v1/dashboard/allocation | 资产配置（饼图数据） |

### 操作日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/logs | 操作日志列表 |

---

## 7. 前端页面（Phase 1）

| 页面 | 路由 | 说明 |
|------|------|------|
| 登录 | /login | 用户名 + 密码登录 |
| 首页总览 | / | 总资产、持仓列表、配置饼图 |
| 记账页 | /trade | 添加持仓、记录交易 |
| 交易历史 | /history | 交易记录列表 |

---

## 8. 项目目录结构

```
family-investment-system/
├── frontend/                    # Next.js 前端
│   ├── src/
│   │   ├── app/                 # App Router 页面
│   │   ├── components/          # UI 组件
│   │   ├── lib/                 # 工具函数、API 客户端
│   │   └── types/               # TypeScript 类型定义
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.js
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   │   └── v1/
│   │   ├── core/                # 配置、安全、依赖注入
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic schema
│   │   ├── services/            # 业务逻辑
│   │   └── main.py              # FastAPI 入口
│   ├── alembic/                 # 数据库迁移
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/
├── docker/                      # Docker 配置
│   ├── nginx/
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
├── docker-compose.yml
├── docs/
│   └── PRD-整体需求文档.md
└── README.md
```

---

## 9. Docker Compose 服务

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| nginx | nginx:alpine | 80/443 | 反向代理 |
| frontend | 自建 | 3000 | Next.js |
| backend | 自建 | 8000 | FastAPI |
| db | postgres:16-alpine | 5432 | PostgreSQL |
| redis | redis:7-alpine | 6379 | Session 缓存 |

---

## 10. 不在 Phase 1 范围

- 行情自动更新（Phase 2）
- Excel 导入（Phase 2）
- 日涨跌显示（Phase 2）
- 每日快照/净值曲线（Phase 2）
- 配置偏离提醒（Phase 2）
- AI 对话（Phase 3）
- 晨报/推送/备忘录（Phase 4）
