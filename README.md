# 网格交易系统（Grid Trading System）

面向 A 股个股与 ETF 的多用户网格交易管理平台，覆盖策略配置、标的绑定、网格明细、定时监控、消息推送、收益分析和模拟回测。

**在线演示：** <https://grid.cnstock1688.cloud/login>

> 当前项目版本对应根目录 [PRD 文档](PRD_网格交易系统.md) 的 v2.12。系统用于辅助记录和判断，**不连接券商、不自动下单，也不构成投资建议**。

## 项目亮点

- **三种预置策略**：震荡向上、标准震荡、震荡向下，支持间距、层数、不对称比例、基准价、止损方式和资金拆分。
- **网格明细自动生成**：按底仓与网格资金生成层号、触发价、方向、数量、金额和状态。
- **定时行情监控**：后台任务轮询腾讯/新浪行情，触发后生成操作记录、站内消息及外部通知。
- **多通道提醒**：企业微信、钉钉 Webhook 和 SMTP 邮件。
- **理论/实际收益对照**：支持录入实际成交，并与理论网格收益进行比较。
- **独立模拟回测**：获取历史 K 线，计算佣金、过户费、印花税、成交、权益曲线与绩效指标。
- **多用户权限隔离**：JWT 登录、角色权限、`self/all` 数据范围与账号有效期。
- **配套管理能力**：公告、文档、系统参数、定时任务和邮件服务配置。

## 策略管理页面

登录后默认进入策略管理页面（`/strategies`），用于完成策略模板选择、网格参数配置、标的绑定和操作明细预览。

| 区域 | 主要功能 |
| --- | --- |
| 策略模板 | 提供震荡向上、标准震荡、震荡向下三种预置模板，展示默认间距、不对称比和层数，可一键套用 |
| 策略列表 | 展示策略名称、模板、绑定标的、基准价、间距、层数、不对称比、网格/底仓资金、切分方式和启用状态 |
| 查询与分页 | 按 ID、名称、模板、标的、基准价、间距、层数、不对称比、资金、切分方式和状态筛选，并支持分页 |
| 新建 / 编辑策略 | 配置名称、模板、标的、基准价、下跌间距、层数、不对称比、止损方式、基准重置周期和资金参数 |
| 资金与份额 | 支持金额切分和份额切分；可分别设置底仓资金、网格资金、买入份额与卖出份额 |
| 策略预览 | 在保存前预览底仓与网格层的层号、方向、触发价、数量、金额和状态 |
| 标的库 | 维护股票、ETF、基金字典及策略绑定关系，支持在线搜索和手工录入 |

页面入口：先访问[在线演示](https://grid.cnstock1688.cloud/login)，登录后进入“策略管理”。

## 技术栈

| 层级 | 主要技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Element Plus、Vue Router、Axios、ECharts |
| 后端 | Python 3.10+、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic |
| 数据库 | MySQL 8.0，`utf8mb4` |
| 任务调度 | APScheduler |
| 行情 | 腾讯/新浪实时行情、东方财富搜索、akshare 与备用 K 线源 |
| 认证与通知 | PBKDF2 密码哈希、HS256 JWT、Webhook、SMTP |

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API
│   │   ├── core/                # 配置、数据库、认证
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── services/            # 网格、行情、监控、回测、通知
│   │   └── main.py              # FastAPI 入口
│   ├── alembic/                 # 数据库版本迁移
│   ├── scripts/init_db.py       # 角色、权限、模板和管理员初始化
│   ├── tests/                   # 后端单元测试
│   ├── .env.example             # 环境变量模板
│   └── requirements.txt
├── frontend/
│   ├── src/                     # Vue 页面、组件、路由和 API 封装
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── Ubuntu部署指南.md
│   └── PRD_网格交易系统_v2.0备份_20260801.md
├── start.bat / stop.bat         # Windows 一键启停
├── start_ubuntu.sh / stop_ubuntu.sh
└── README.md
```

运行期生成或本机专用的 `.env`、日志、上传文件、`node_modules`、虚拟环境和 `frontend/dist` 已由 `.gitignore` 排除，不应提交。

## 快速开始（Windows）

### 1. 准备环境

需要安装：

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- MySQL 8.0

确认命令可用：

```powershell
python --version
node --version
npm --version
mysql --version
```

### 2. 创建数据库

用 MySQL 管理员账号登录后执行，密码请替换为强密码：

```sql
CREATE DATABASE IF NOT EXISTS grid_trading
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'grid_app'@'localhost' IDENTIFIED BY '替换为强密码';
GRANT ALL PRIVILEGES ON grid_trading.* TO 'grid_app'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置并启动后端

以下命令必须在 PowerShell 中执行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

在打开的 `.env` 中至少填写数据库密码和 `JWT_SECRET`。可用下面的 PowerShell 命令生成随机密钥，再把结果粘贴到 `.env`：

```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
```

执行数据库迁移和初始化：

```powershell
alembic upgrade head
python scripts\init_db.py --admin-username admin --admin-phone 13800000000
```

初始化脚本会创建预置角色、权限、三种策略模板和默认系统参数，并提示输入管理员密码。脚本可重复执行，不会覆盖已有业务数据。

启动 API：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- 健康检查：<http://127.0.0.1:8000/health>
- Swagger 文档：<http://127.0.0.1:8000/docs>

### 4. 启动前端

另开一个 PowerShell 窗口：

```powershell
cd frontend
npm ci
npm run dev
```

打开 <http://localhost:5173>，使用初始化时创建的管理员账号登录。

完成首次安装后，也可以在项目根目录双击 `start.bat` 同时启动前后端，双击 `stop.bat` 停止。

## 配置说明

`backend/.env` 的主要配置项：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DB_HOST` | 是 | MySQL 地址，默认 `127.0.0.1` |
| `DB_PORT` | 是 | MySQL 端口，默认 `3306` |
| `DB_USER` | 是 | 数据库账号 |
| `DB_PASSWORD` | 是 | 数据库密码 |
| `DB_NAME` | 是 | 数据库名，默认 `grid_trading` |
| `MARKET_DATA_MODE` | 是 | `mock` 模拟行情或 `real` 真实行情 |
| `JWT_SECRET` | 生产必填 | JWT 签名密钥；缺失时进程会使用临时随机值，重启后登录态失效 |
| `DINGTALK_WEBHOOK` | 否 | 钉钉机器人 Webhook |
| `WECHAT_WEBHOOK` | 否 | 企业微信机器人 Webhook |
| `APP_HOST` / `APP_PORT` | 否 | 服务监听地址与端口 |

SMTP 发件配置由管理员在页面中维护，用户收件地址在监控配置中维护。

## 测试与构建

后端测试：

```powershell
cd backend
python -m unittest discover -s tests -v
```

前端生产构建：

```powershell
cd frontend
npm run build
```

构建结果输出到 `frontend/dist`，该目录不进入 Git。

## 数据与数据库迁移

数据库结构由 `backend/alembic/versions/` 管理：

```powershell
cd backend
alembic current
alembic upgrade head
```

应用启动时会调用 `create_all` 兜底建表，但生产环境仍应以 Alembic 迁移结果为准。`backend/migrate_v21.py` 至 `migrate_v24.py` 是历史版本的一次性迁移脚本，仅用于升级指定旧库；新部署不需要执行。

## Ubuntu 部署

启动/停止辅助脚本：

```bash
chmod +x start_ubuntu.sh stop_ubuntu.sh
./start_ubuntu.sh
./stop_ubuntu.sh
```

Nginx、HTTPS、systemd、数据备份和回滚步骤见 [Ubuntu 部署指南](docs/Ubuntu部署指南.md)。

## 安全说明

- 不要提交 `backend/.env`、数据库备份、`backend/uploads/` 或任何真实 Webhook、邮箱授权码。
- 生产环境必须设置高强度 `JWT_SECRET`，并限制 `.env` 文件权限。
- SMTP 密码和 Webhook URL 当前存储在系统参数/数据库中，请使用专用低权限账号，并限制数据库访问。
- 建议只在本机或受信任内网使用；若暴露公网，请配置 HTTPS、反向代理、防火墙、备份和登录限流。
- 请先使用 `MARKET_DATA_MODE=mock` 验证流程，再切换真实行情。

## 已知边界

- 行情和回测结果依赖第三方数据源，可能延迟、缺失或调整口径。
- 网格触发是辅助记录与提醒，不会向券商发送委托。
- 本项目当前未声明开源许可证；对外发布或商用前请先确定授权方式。

## 相关文档

- [产品需求文档](PRD_网格交易系统.md)
- [Ubuntu 部署指南](docs/Ubuntu部署指南.md)
- [策略参数设置方案](<网格交易：震荡向上  震荡向下 间距、不对称比例完整设置方案.md>)
- [原始需求](原始需求.md)
