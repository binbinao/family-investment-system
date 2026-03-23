# Phase 1 实施计划 — "能用"

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建项目骨架，实现用户登录、持仓 CRUD、交易记录、首页总览，Docker Compose 一键部署。

**Architecture:** Next.js 14+ 前端 + FastAPI 后端，前后端分离通过 REST API 通信。PostgreSQL 存储数据，Redis 管理 Session。Docker Compose 编排全部服务。

**Tech Stack:** Next.js 14+, TypeScript, shadcn/ui, Tailwind CSS, Recharts, FastAPI, Python 3.11+, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, Redis 7, Docker Compose

**Spec:** `docs/superpowers/specs/2026-03-23-phase1-design.md`

---

## 文件结构总览

```
family-investment-system/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                # 根布局
│   │   │   ├── page.tsx                  # 首页/总览
│   │   │   ├── login/page.tsx            # 登录页
│   │   │   ├── trade/page.tsx            # 记账页（添加持仓+交易）
│   │   │   └── history/page.tsx          # 交易历史
│   │   ├── components/
│   │   │   ├── ui/                       # shadcn/ui 组件（自动生成）
│   │   │   ├── layout/
│   │   │   │   ├── header.tsx            # 顶部导航
│   │   │   │   └── auth-guard.tsx        # 登录保护
│   │   │   ├── dashboard/
│   │   │   │   ├── summary-cards.tsx     # 总资产卡片
│   │   │   │   ├── holdings-table.tsx    # 持仓列表表格
│   │   │   │   └── allocation-chart.tsx  # 资产配置饼图
│   │   │   ├── holdings/
│   │   │   │   ├── add-holding-form.tsx  # 添加持仓表单
│   │   │   │   ├── edit-holding-dialog.tsx # 编辑持仓弹窗
│   │   │   │   └── update-price-dialog.tsx # 更新价格弹窗
│   │   │   └── transactions/
│   │   │       ├── add-transaction-form.tsx # 记录交易表单
│   │   │       └── transaction-list.tsx    # 交易历史列表
│   │   ├── lib/
│   │   │   ├── api.ts                    # API 客户端封装
│   │   │   └── utils.ts                  # 工具函数（格式化等）
│   │   └── types/
│   │       └── index.ts                  # TypeScript 类型定义
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── postcss.config.js
│   └── .env.local.example
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI 入口
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # 配置（环境变量）
│   │   │   ├── database.py               # 数据库连接
│   │   │   ├── redis.py                  # Redis 连接
│   │   │   ├── security.py               # 密码哈希、Session
│   │   │   └── deps.py                   # 依赖注入
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── holding.py
│   │   │   ├── transaction.py
│   │   │   └── operation_log.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── holding.py
│   │   │   ├── transaction.py
│   │   │   └── dashboard.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── holding.py
│   │   │   ├── transaction.py
│   │   │   └── dashboard.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── router.py             # 总路由
│   │           ├── auth.py
│   │           ├── holdings.py
│   │           ├── transactions.py
│   │           └── dashboard.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── scripts/
│   │   └── init_users.py                 # 初始化用户脚本
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_holdings.py
│       ├── test_transactions.py
│       └── test_dashboard.py
├── docker/
│   ├── nginx/
│   │   └── nginx.conf
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Task 1: 后端项目骨架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/redis.py`

- [ ] **Step 1: 创建 backend 目录和 requirements.txt**

```
backend/requirements.txt:

fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
alembic==1.13.3
redis==5.2.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
pydantic==2.9.0
pydantic-settings==2.5.0
httpx==0.27.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 2: 创建配置模块 `backend/app/core/config.py`**

通过 pydantic-settings 从环境变量读取配置：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_invest"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    SESSION_EXPIRE_HOURS: int = 168  # 7 days
    
    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: 创建数据库连接模块 `backend/app/core/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: 创建 Redis 连接模块 `backend/app/core/redis.py`**

```python
import redis.asyncio as redis

redis_client: redis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL)

async def close_redis():
    if redis_client:
        await redis_client.close()

def get_redis() -> redis.Redis:
    return redis_client
```

- [ ] **Step 5: 创建 FastAPI 入口 `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()

app = FastAPI(title="齐家·家庭投资助手", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], ...)
```

- [ ] **Step 6: 验证后端启动**

Run: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
Expected: FastAPI 启动成功，访问 http://localhost:8000/docs 看到 Swagger 文档

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: 初始化 FastAPI 后端项目骨架"
```

---

## Task 2: 数据库模型和迁移

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/holding.py`
- Create: `backend/app/models/transaction.py`
- Create: `backend/app/models/operation_log.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: 创建 User 模型**

```python
# backend/app/models/user.py
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 创建 Holding 模型**

```python
# backend/app/models/holding.py
class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(20), nullable=False)  # 股票/基金/债券/现金/其他
    quantity = Column(Numeric(18, 4), nullable=False)
    cost_price = Column(Numeric(18, 4), nullable=False)
    latest_price = Column(Numeric(18, 4))
    latest_price_updated_at = Column(DateTime)
    account = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 3: 创建 Transaction 模型**

```python
# backend/app/models/transaction.py
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    holding_id = Column(UUID(as_uuid=True), ForeignKey("holdings.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False)  # 买入/卖出/现金分红/红利再投资
    quantity = Column(Numeric(18, 4), nullable=False)
    price = Column(Numeric(18, 4), nullable=False)
    fee = Column(Numeric(18, 4), default=0)
    realized_pnl = Column(Numeric(18, 4))
    date = Column(Date, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: 创建 OperationLog 模型**

```python
# backend/app/models/operation_log.py
class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 5: 模型 `__init__.py` 统一导出**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.holding import Holding
from app.models.transaction import Transaction
from app.models.operation_log import OperationLog
```

- [ ] **Step 6: 初始化 Alembic**

Run: `cd backend && alembic init alembic`

修改 `alembic/env.py`，配置 async 引擎 + 导入所有模型。
修改 `alembic.ini`，设置 `sqlalchemy.url`。

- [ ] **Step 7: 生成初始迁移**

Run: `cd backend && alembic revision --autogenerate -m "initial tables"`
Expected: 生成迁移文件，包含 users/holdings/transactions/operation_logs 四张表

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/ backend/alembic/ backend/alembic.ini
git commit -m "feat: 添加数据库模型和 Alembic 迁移"
```

---

## Task 3: 认证系统

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/deps.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/scripts/init_users.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: 创建安全模块 `backend/app/core/security.py`**

密码哈希（bcrypt）和 Session 管理（Redis）：

```python
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_session_id() -> str:
    return secrets.token_urlsafe(64)
```

Session CRUD（存/取/删 Redis）。

- [ ] **Step 2: 创建认证 Schema `backend/app/schemas/auth.py`**

```python
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    display_name: str | None
```

- [ ] **Step 3: 创建认证 Service `backend/app/services/auth.py`**

登录逻辑：查用户 → 验密码 → 创建 Session → 返回 session_id。

- [ ] **Step 4: 创建依赖注入 `backend/app/core/deps.py`**

`get_current_user`：从 Cookie 读 session_id → Redis 查 user_id → 数据库查 User。未登录返回 401。

- [ ] **Step 5: 创建认证 API `backend/app/api/v1/auth.py`**

POST /login, POST /logout, GET /me。登录成功设置 Cookie。

- [ ] **Step 6: 创建路由总入口 `backend/app/api/v1/router.py`**

```python
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
```

在 main.py 中挂载: `app.include_router(api_router, prefix="/api/v1")`

- [ ] **Step 7: 创建初始化用户脚本 `backend/scripts/init_users.py`**

创建默认用户（如 admin/admin123），用于开发测试。

- [ ] **Step 8: 编写认证测试 `backend/tests/test_auth.py`**

测试：登录成功、密码错误、获取当前用户、登出。

- [ ] **Step 9: 运行测试**

Run: `cd backend && pytest tests/test_auth.py -v`
Expected: 全部通过

- [ ] **Step 10: Commit**

```bash
git add backend/app/core/security.py backend/app/core/deps.py backend/app/schemas/ backend/app/services/auth.py backend/app/api/ backend/scripts/ backend/tests/
git commit -m "feat: 实现用户认证（登录/登出/Session）"
```

---

## Task 4: 持仓 CRUD API

**Files:**
- Create: `backend/app/schemas/holding.py`
- Create: `backend/app/services/holding.py`
- Create: `backend/app/api/v1/holdings.py`
- Test: `backend/tests/test_holdings.py`

- [ ] **Step 1: 创建持仓 Schema `backend/app/schemas/holding.py`**

```python
class HoldingCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str  # 股票/基金/债券/现金/其他
    quantity: Decimal
    cost_price: Decimal
    latest_price: Decimal | None = None
    account: str | None = None

class HoldingUpdate(BaseModel):
    name: str | None = None
    quantity: Decimal | None = None
    cost_price: Decimal | None = None
    account: str | None = None

class HoldingPriceUpdate(BaseModel):
    latest_price: Decimal

class HoldingResponse(BaseModel):
    id: UUID
    symbol: str
    name: str
    asset_type: str
    quantity: Decimal
    cost_price: Decimal
    latest_price: Decimal | None
    latest_price_updated_at: datetime | None
    account: str | None
    market_value: Decimal | None    # 计算字段：quantity * latest_price
    profit_loss: Decimal | None     # 计算字段：market_value - total_cost
    profit_loss_pct: float | None   # 计算字段：盈亏百分比
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: 创建持仓 Service `backend/app/services/holding.py`**

CRUD 操作 + 盈亏计算逻辑：
- `list_holdings()` — 返回所有持仓（含计算字段）
- `create_holding()` — 新增持仓 + 操作日志
- `update_holding()` — 编辑持仓 + 操作日志
- `delete_holding()` — 删除持仓 + 操作日志
- `update_price()` — 更新最新价格

- [ ] **Step 3: 创建持仓 API `backend/app/api/v1/holdings.py`**

GET /holdings, POST /holdings, PUT /holdings/{id}, DELETE /holdings/{id}, PATCH /holdings/{id}/price

所有接口需要登录（依赖 get_current_user）。

- [ ] **Step 4: 注册路由到 router.py**

```python
api_router.include_router(holdings_router, prefix="/holdings", tags=["持仓"])
```

- [ ] **Step 5: 编写持仓测试 `backend/tests/test_holdings.py`**

测试：创建持仓、列表查询、编辑、删除、更新价格、盈亏计算。

- [ ] **Step 6: 运行测试**

Run: `cd backend && pytest tests/test_holdings.py -v`
Expected: 全部通过

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/holding.py backend/app/services/holding.py backend/app/api/v1/holdings.py backend/tests/test_holdings.py
git commit -m "feat: 实现持仓 CRUD API"
```

---

## Task 5: 交易记录 API

**Files:**
- Create: `backend/app/schemas/transaction.py`
- Create: `backend/app/services/transaction.py`
- Create: `backend/app/api/v1/transactions.py`
- Test: `backend/tests/test_transactions.py`

- [ ] **Step 1: 创建交易 Schema `backend/app/schemas/transaction.py`**

```python
class TransactionCreate(BaseModel):
    holding_id: UUID
    type: str        # 买入/卖出/现金分红/红利再投资
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    date: date

class TransactionResponse(BaseModel):
    id: UUID
    holding_id: UUID
    symbol: str
    type: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal | None
    date: date
    user_id: UUID
    created_at: datetime
```

- [ ] **Step 2: 创建交易 Service `backend/app/services/transaction.py`**

核心逻辑 — 记录交易并自动更新持仓：

```python
async def create_transaction(data, user_id, db):
    holding = await get_holding(data.holding_id)
    
    if data.type == "买入":
        # 移动加权平均：new_cost = (old_qty * old_cost + new_qty * new_price) / (old_qty + new_qty)
        new_quantity = holding.quantity + data.quantity
        new_cost = (holding.quantity * holding.cost_price + data.quantity * data.price) / new_quantity
        holding.quantity = new_quantity
        holding.cost_price = new_cost
    
    elif data.type == "卖出":
        if data.quantity > holding.quantity:
            raise ValueError("卖出数量超过持仓")
        realized_pnl = (data.price - holding.cost_price) * data.quantity - data.fee
        holding.quantity -= data.quantity
        # 成本价不变
    
    elif data.type == "现金分红":
        # 不影响持仓数量，记录现金流入
        realized_pnl = data.quantity * data.price  # quantity=1, price=分红金额
    
    elif data.type == "红利再投资":
        # 增加数量，成本价摊薄
        new_quantity = holding.quantity + data.quantity
        holding.cost_price = (holding.quantity * holding.cost_price) / new_quantity
        holding.quantity = new_quantity
```

- [ ] **Step 3: 创建交易 API `backend/app/api/v1/transactions.py`**

GET /transactions (支持 ?holding_id= 过滤), POST /transactions

- [ ] **Step 4: 注册路由**

```python
api_router.include_router(transactions_router, prefix="/transactions", tags=["交易"])
```

- [ ] **Step 5: 编写交易测试 `backend/tests/test_transactions.py`**

测试：买入更新成本、卖出计算盈亏、卖出超量报错、现金分红、红利再投资摊薄成本。

- [ ] **Step 6: 运行测试**

Run: `cd backend && pytest tests/test_transactions.py -v`
Expected: 全部通过

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/transaction.py backend/app/services/transaction.py backend/app/api/v1/transactions.py backend/tests/test_transactions.py
git commit -m "feat: 实现交易记录 API（含持仓自动更新）"
```

---

## Task 6: Dashboard API（总览数据）

**Files:**
- Create: `backend/app/schemas/dashboard.py`
- Create: `backend/app/services/dashboard.py`
- Create: `backend/app/api/v1/dashboard.py`
- Test: `backend/tests/test_dashboard.py`

- [ ] **Step 1: 创建 Dashboard Schema**

```python
class DashboardSummary(BaseModel):
    total_market_value: Decimal     # 总市值
    total_cost: Decimal             # 总成本
    total_profit_loss: Decimal      # 总盈亏
    total_profit_loss_pct: float    # 总收益率
    holdings_count: int             # 持仓数量

class AllocationItem(BaseModel):
    asset_type: str
    market_value: Decimal
    percentage: float
```

- [ ] **Step 2: 创建 Dashboard Service**

聚合计算：遍历所有持仓，汇总市值/成本/盈亏，按资产类型分组计算占比。

- [ ] **Step 3: 创建 Dashboard API**

GET /dashboard/summary, GET /dashboard/allocation

- [ ] **Step 4: 注册路由**

- [ ] **Step 5: 编写测试**

- [ ] **Step 6: 运行测试**

Run: `cd backend && pytest tests/test_dashboard.py -v`
Expected: 全部通过

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/dashboard.py backend/app/services/dashboard.py backend/app/api/v1/dashboard.py backend/tests/test_dashboard.py
git commit -m "feat: 实现首页总览 API（资产汇总+配置占比）"
```

---

## Task 7: 前端项目骨架

**Files:**
- Create: `frontend/` 整个 Next.js 项目
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 初始化 Next.js 项目**

Run: `cd frontend && npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"`

- [ ] **Step 2: 安装 shadcn/ui**

Run: `cd frontend && npx shadcn@latest init`

然后安装需要的组件：

Run: `npx shadcn@latest add button card input label table dialog form select toast dropdown-menu`

- [ ] **Step 3: 安装 Recharts**

Run: `cd frontend && npm install recharts`

- [ ] **Step 4: 创建 TypeScript 类型定义 `frontend/src/types/index.ts`**

定义 Holding, Transaction, DashboardSummary, AllocationItem 等类型，与后端 Schema 对应。

- [ ] **Step 5: 创建 API 客户端 `frontend/src/lib/api.ts`**

封装 fetch，统一处理错误、Cookie 传递、JSON 解析：

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  auth: {
    login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    logout: () => request("/auth/logout", { method: "POST" }),
    me: () => request("/auth/me"),
  },
  holdings: { ... },
  transactions: { ... },
  dashboard: { ... },
};
```

- [ ] **Step 6: 创建工具函数 `frontend/src/lib/utils.ts`**

数字格式化（金额、百分比）、颜色（盈亏红绿）等。

- [ ] **Step 7: 创建 .env.local.example**

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: 初始化 Next.js 前端项目骨架"
```

---

## Task 8: 前端登录页

**Files:**
- Create: `frontend/src/app/login/page.tsx`
- Create: `frontend/src/components/layout/auth-guard.tsx`
- Modify: `frontend/src/app/layout.tsx`

- [ ] **Step 1: 创建登录页 `frontend/src/app/login/page.tsx`**

简洁的登录表单：用户名 + 密码 + 登录按钮。使用 shadcn/ui Card, Input, Button, Label 组件。登录成功跳转首页。

- [ ] **Step 2: 创建认证守卫 `frontend/src/components/layout/auth-guard.tsx`**

客户端组件，挂载时调用 GET /auth/me。未登录重定向到 /login。

- [ ] **Step 3: 创建顶部导航 `frontend/src/components/layout/header.tsx`**

显示产品名称、当前用户、导航链接（首页/记账/交易历史）、登出按钮。

- [ ] **Step 4: 修改根布局 `frontend/src/app/layout.tsx`**

集成 AuthGuard 和 Header（登录页除外）。

- [ ] **Step 5: 验证登录流程**

启动前后端，手动测试：访问首页 → 跳转登录 → 登录 → 进入首页 → 登出。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现前端登录页和认证守卫"
```

---

## Task 9: 前端首页（总览）

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/dashboard/summary-cards.tsx`
- Create: `frontend/src/components/dashboard/holdings-table.tsx`
- Create: `frontend/src/components/dashboard/allocation-chart.tsx`

- [ ] **Step 1: 创建总资产卡片组件 `summary-cards.tsx`**

四张卡片：总市值、总成本、总盈亏（金额+百分比，红涨绿跌）、持仓数量。使用 shadcn/ui Card。

- [ ] **Step 2: 创建持仓列表表格 `holdings-table.tsx`**

表格列：标的代码、名称、类型、数量、成本价、最新价、市值、盈亏、盈亏%、占比。
每行支持：编辑、删除、更新价格操作。使用 shadcn/ui Table。

- [ ] **Step 3: 创建资产配置饼图 `allocation-chart.tsx`**

使用 Recharts PieChart，按资产类型展示配置比例，显示百分比标签。

- [ ] **Step 4: 组装首页 `frontend/src/app/page.tsx`**

调用 Dashboard API 和 Holdings API，展示：SummaryCards → AllocationChart → HoldingsTable。

- [ ] **Step 5: 验证首页展示**

启动前后端，手动添加几条持仓（通过 API），验证首页正确显示数据。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现首页总览（资产卡片+持仓表格+配置饼图）"
```

---

## Task 10: 前端记账页

**Files:**
- Create: `frontend/src/app/trade/page.tsx`
- Create: `frontend/src/components/holdings/add-holding-form.tsx`
- Create: `frontend/src/components/holdings/edit-holding-dialog.tsx`
- Create: `frontend/src/components/holdings/update-price-dialog.tsx`
- Create: `frontend/src/components/transactions/add-transaction-form.tsx`

- [ ] **Step 1: 创建添加持仓表单 `add-holding-form.tsx`**

表单字段：标的代码、名称、资产类型（下拉选择）、数量、成本价、账户（可选）。使用 shadcn/ui Form 组件，含表单校验。

- [ ] **Step 2: 创建记录交易表单 `add-transaction-form.tsx`**

表单字段：选择持仓（下拉）、交易类型（买入/卖出/现金分红/红利再投资）、数量、价格、手续费（可选）、交易日期。提交后自动更新持仓。

- [ ] **Step 3: 创建编辑持仓弹窗 `edit-holding-dialog.tsx`**

Dialog 表单，可修改名称、数量、成本价、账户。

- [ ] **Step 4: 创建更新价格弹窗 `update-price-dialog.tsx`**

Dialog 表单，输入最新价格，提交后更新。

- [ ] **Step 5: 组装记账页 `frontend/src/app/trade/page.tsx`**

两个 Tab 或两个区域：添加持仓 + 记录交易。

- [ ] **Step 6: 验证记账流程**

手动测试：添加持仓 → 记录买入 → 查看持仓变化 → 记录卖出 → 查看盈亏计算。

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现记账页（添加持仓+记录交易）"
```

---

## Task 11: 前端交易历史页

**Files:**
- Create: `frontend/src/app/history/page.tsx`
- Create: `frontend/src/components/transactions/transaction-list.tsx`

- [ ] **Step 1: 创建交易列表组件 `transaction-list.tsx`**

表格列：日期、标的、类型、数量、价格、手续费、实现盈亏。支持按标的过滤。

- [ ] **Step 2: 组装交易历史页 `frontend/src/app/history/page.tsx`**

顶部过滤器 + 交易列表。

- [ ] **Step 3: 验证交易历史展示**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现交易历史页"
```

---

## Task 12: Docker Compose 部署

**Files:**
- Create: `docker-compose.yml`
- Create: `docker/Dockerfile.frontend`
- Create: `docker/Dockerfile.backend`
- Create: `docker/nginx/nginx.conf`
- Create: `.env.example`
- Create: `backend/scripts/init_users.py`（如尚未创建）

- [ ] **Step 1: 创建后端 Dockerfile**

```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建前端 Dockerfile**

```dockerfile
# docker/Dockerfile.frontend
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

- [ ] **Step 3: 创建 nginx 配置**

反向代理：/ → frontend:3000，/api → backend:8000。

- [ ] **Step 4: 创建 docker-compose.yml**

5 个服务：nginx, frontend, backend, db (postgres), redis。
配置 volumes（数据库持久化）、depends_on、环境变量。

- [ ] **Step 5: 创建 .env.example**

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=family_invest
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me-in-production
```

- [ ] **Step 6: 验证 Docker Compose 启动**

Run: `docker compose up --build`
Expected: 全部服务启动成功，访问 http://localhost 看到登录页

- [ ] **Step 7: 验证数据库迁移和用户初始化**

Run: `docker compose exec backend alembic upgrade head && docker compose exec backend python scripts/init_users.py`
Expected: 数据库表创建成功，初始用户创建成功

- [ ] **Step 8: 端到端验证**

手动测试完整流程：登录 → 添加持仓 → 记录交易 → 查看首页总览 → 查看交易历史。

- [ ] **Step 9: Commit**

```bash
git add docker/ docker-compose.yml .env.example
git commit -m "feat: 添加 Docker Compose 一键部署配置"
```

---

## Task 13: 测试完善和最终验证

- [ ] **Step 1: 补充后端测试 conftest.py**

创建测试数据库 fixture、测试用户 fixture、测试客户端 fixture。

- [ ] **Step 2: 运行全部后端测试**

Run: `cd backend && pytest tests/ -v --tb=short`
Expected: 全部通过

- [ ] **Step 3: 端到端流程验证**

使用 Docker Compose 启动全部服务，完整走一遍：
1. 登录
2. 添加 3 只持仓（股票、基金、其他各一只）
3. 手动更新价格
4. 记录买入交易
5. 记录卖出交易，验证盈亏计算
6. 首页查看总资产、饼图
7. 查看交易历史
8. 登出

- [ ] **Step 4: 最终 Commit**

```bash
git add .
git commit -m "feat: Phase 1 完成 — 持仓管理和首页总览"
```
