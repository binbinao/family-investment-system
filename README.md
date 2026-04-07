# 齐家 · 家庭投资助手

给三口之家用的投资记账本 + AI 分析助手。记清楚家里买了什么、赚了还是亏了、下一步怎么办。

## 解决什么问题

| 痛点 | 方案 |
|------|------|
| **记不清** — 持仓散落在多个 App，不知道一共投了多少 | 家庭资产总览，一眼看清全部持仓 |
| **看不懂** — 想分析标的，不知道从哪入手 | AI 驱动的个股分析和每日晨报 |
| **没人聊** — 想跟家人讨论，缺少共享信息基础 | 家庭共享视图，同一份数据多人查看 |

## 核心功能

- **家庭资产总览**：总市值、盈亏、日涨跌、配置饼图
- **持仓与交易管理**：手动录入 / Excel 批量导入，行情自动更新
- **AI 分析助手**：每日晨报、个股深度分析、自然语言问答
- **家庭共享**：多人共享同一份数据，操作日志可追溯

## 技术栈

- **前端**：Next.js 14+ / TypeScript / Tailwind CSS / shadcn/ui
- **后端**：FastAPI (Python 3.11+)
- **数据库**：PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **缓存**：Redis 7（Session 存储 + 行情缓存）
- **AI**：DeepSeek API
- **行情数据**：AKShare（开源）
- **部署**：Docker Compose 一键部署

## 容器化环境配置（Docker Compose）

以下流程用于在本机用容器一键拉起 **Nginx + 前端 + 后端 + PostgreSQL + Redis**。后端启动时会自动执行 **Alembic 迁移** 并尝试初始化默认账号（见下文）。

### 1. 前置条件

- 已安装 [Docker](https://docs.docker.com/get-docker/) 与 **Docker Compose V2**（`docker compose` 命令可用）。
- 本机内存建议 **≥ 4GB**（首次构建前端会占用较多资源）。
- **80 端口**未被占用；若被占用，见下文「端口与重建前端镜像」。

### 2. 获取代码并准备环境变量

```bash
git clone https://github.com/binbinao/family-investment-system.git
cd family-investment-system
cp .env.example .env
```

用编辑器打开项目根目录的 `.env`，至少完成：

| 变量 | 说明 |
|------|------|
| `POSTGRES_PASSWORD` | 数据库密码，**不要用仓库默认值**，请改为强密码。 |
| `SECRET_KEY` | 后端会话/签名密钥，**生产或公网暴露前必须改为随机长字符串**。 |
| `DEEPSEEK_API_KEY` | DeepSeek 官方 API Key；若走第三方兼容网关，可配置 `DEEPSEEK_VENDOR_*` 一组（见 `.env.example` 内注释）。 |
| `NGINX_HOST_PORT` | 浏览器访问站点时使用的**本机端口**，默认 `80`。若本机 80 已被占用，改为例如 `8080` 或 `8888`。 |

可选：在 `docker-compose.yml` 中还可通过 `POSTGRES_HOST_PORT`、`REDIS_HOST_PORT` 把数据库/Redis 映射到本机其他端口（便于本地工具连接）；未改 compose 时一般无需设置。

### 3. 构建并启动

在项目根目录执行：

```bash
docker compose build
docker compose up -d
```

首次构建会安装依赖并编译 Next.js，可能需数分钟。查看日志：

```bash
docker compose logs -f
```

### 4. 访问与验证

- **站点（经 Nginx）**：浏览器打开 `http://localhost:<NGINX_HOST_PORT>`（默认即 `http://localhost` 或 `http://localhost:80`）。
- **后端健康检查**：`http://localhost:<NGINX_HOST_PORT>/health`
- **API 文档（Swagger）**：`http://localhost:<NGINX_HOST_PORT>/docs`

数据持久化在 Docker 卷 `postgres_data`、`redis_data` 中；`docker compose down` **不会**删除卷内数据，除非显式加 `-v`。

### 5. 默认账号（首次初始化）

后端入口脚本会运行 `scripts/init_users.py`（已存在用户则跳过）。默认包括：

| 用户名 | 密码 | 说明 |
|--------|------|------|
| `admin` | `admin123` | 管理员 |
| `family1` / `family2` | `family123` | 家人账号 |

**登录后请立即在系统内修改密码**；若部署在可被他人访问的环境，请勿长期使用默认口令。

### 6. 常用运维命令

```bash
# 停止容器（保留数据卷）
docker compose down

# 停止并删除数据卷（清空数据库与 Redis 数据，慎用）
docker compose down -v

# 修改代码后重新构建并启动
docker compose build --no-cache
docker compose up -d
```

### 7. 端口与重建前端镜像

前端镜像构建时会将 `NEXT_PUBLIC_API_URL` 写死为 `http://localhost:<NGINX_HOST_PORT>/api/v1`（与 `docker-compose.yml` 中 `args` 一致）。因此：

- **若你在首次构建前修改了 `NGINX_HOST_PORT`**，直接 `docker compose build` 即可。
- **若构建完成后才改 `NGINX_HOST_PORT`**，需要重新构建前端镜像，例如：

```bash
docker compose build frontend
docker compose up -d
```

否则浏览器里前端仍可能请求旧的 API 地址。

### 8. 故障排查简要

- **容器反复重启**：查看 `docker compose logs backend` 是否数据库连接失败（检查 `.env` 中密码与 `POSTGRES_*` 是否与 compose 一致）。
- **AI 功能不可用**：确认 `.env` 中已配置有效的 `DEEPSEEK_API_KEY` 或完整的 `DEEPSEEK_VENDOR_*`，修改后执行 `docker compose up -d` 使后端环境变量生效。
- **80 端口占用**：将 `NGINX_HOST_PORT` 改为空闲端口并按上一节重建 `frontend` 后再访问新端口。

## 页面清单

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页总览 | `/` | 资产总览、净值曲线、配置偏离提醒、行情状态 |
| 记账 | `/trade` | 添加持仓、记录交易、Excel 批量导入 |
| AI 对话 | `/ai` | 快问/深聊两种模式，SSE 流式输出 |
| 晨报 | `/reports` | 每日 AI 晨报列表、详情查看 |
| 备忘录 | `/memos` | 家庭投资备忘，支持 #代码 关联标的 |
| 配置目标 | `/allocation` | 资产配置目标比例设定 |
| 设置 | `/settings` | 推送通知配置（Server酱/Bark/邮件） |

## 项目状态

全部 4 个 Phase 开发完成（能用 → 好用 → 聪明 → 完整）

## 许可证

私有项目，仅供家庭内部使用。
