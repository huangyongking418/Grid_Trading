# 网格交易系统 Ubuntu 部署指南

本文档覆盖从本地（Windows 开发机）迁移到 Ubuntu 服务器的完整流程：环境准备、数据库迁移、后端部署、前端部署、Nginx、HTTPS、备份与回滚。

---

## 1. 部署前准备 

### 1.1 服务器要求

- 操作系统：Ubuntu 22.04 / 24.04（LTS）
- 内存：建议 2GB 以上
- 磁盘：20GB 以上（行情缓存与上传文件会增长）
- 开放端口：SSH 22、HTTP 80、HTTPS 443
- 可选：一个域名（不配域名也可以用服务器 IP 访问）

### 1.2 本地迁移清单

#### 需要迁移

| 类别 | 具体文件 / 目录 | 说明 |
|------|----------------|------|
| 后端源码 | `backend/app/` | 全部 API 路由、ORM 模型、业务服务与 FastAPI 主入口 |
| 数据库迁移 | `backend/alembic/`、`backend/alembic.ini` | 表结构迁移脚本，导入旧库后由 Alembic 校验版本 |
| 后端依赖 | `backend/requirements.txt` | 服务器上 `pip install -r requirements.txt` 使用 |
| 配置模板 | `backend/.env.example` | 服务器上 `cp .env.example .env` 后再修改 |
| 上传数据 | `backend/uploads/announcements/`、`backend/uploads/documents/` | 公告图片、系统文档等运行时数据，只迁移实际文件 |
| 前端源码 | `frontend/src/`、`frontend/index.html`、`frontend/vite.config.js` | Vue 页面、组件、路由与构建配置 |
| 前端依赖 | `frontend/package.json`、`frontend/package-lock.json` | 服务器上 `npm install` 使用，锁文件保证依赖版本一致 |
| Ubuntu 脚本 | `start_ubuntu.sh`、`stop_ubuntu.sh` | 服务器端启动 / 停止服务使用 |
| 资料文档（可选） | `docs/`、`README.md`、`PRD_网格交易系统.md`、`原始需求.md` | 不参与运行，仅作部署与排障参考 |
| 数据库数据 | `grid_trading_backup.sql`（第 2.1 节导出的文件） | 服务器导入到 MySQL |

> 注意：迁移的是 `backend/.env.example` 模板，不是 `backend/.env`。`.env` 含本机数据库密码等敏感配置，直接随源码迁移有泄露风险，应在服务器上重新创建。

#### 不需要迁移

| 文件 / 目录 | 原因 |
|-------------|------|
| `backend/.env` | 含本机敏感配置；只用 `.env.example` 在服务器重建 |
| `backend/venv/` | 虚拟环境与当前系统绑定，服务器重新创建 |
| `backend/__pycache__/`、`backend/app/**/__pycache__/`、`backend/alembic/**/__pycache__/` | Python 字节码缓存，运行自动生成 |
| `frontend/node_modules/` | 由 `npm install` 在服务器生成 |
| `frontend/dist/` | 构建产物，由服务器 `npm run build` 生成 |
| `logs/`、`.run/` | 运行日志与 PID 文件，启动脚本会自动创建 |
| `backend/start_error.log`、`frontend/start_error.log`、`backend_error.log` | 本机排错日志，与运行无关 |
| `start.bat`、`start_backend.bat`、`stop.bat` | Windows 专用脚本，Ubuntu 使用 `.sh` 脚本或 systemd |
| `backend/start_backend.py`、`frontend/start_frontend.py` | Windows 开发启动辅助，生产环境不需要 |
| `migrate_v21.py`、`migrate_v22.py`、`migrate_v23.py`、`fix_param_desc.py` | 历史一次性数据迁移 / 修复脚本；数据库已用 mysqldump 全量导出，服务器无需再执行（可选保留作历史记录） |
| `backend/tests/` | 单元测试，非生产运行必需（可选迁移，便于服务器上复测） |

---

## 2. 本地数据导出 （不要）

### 2.1 导出 MySQL 数据库 （dbever导出）

在 Windows 开发机上执行（用实际 MySQL 账号密码）：

```powershell
mysqldump -u root -p --databases grid_trading --single-transaction --routines --triggers > grid_trading_backup.sql
```

导出的 SQL 文件包含所有表和 `alembic_version`，服务器导入后无需再跑迁移（除非代码里有更新的迁移版本）。

### 2.2 打包上传目录

```powershell
tar -czf uploads_backup.tar.gz backend\uploads
```

### 2.3 传输到服务器

在 Windows 上使用 scp（或任意 SFTP 工具）：

```powershell
scp -r .\backend\app .\backend\alembic .\backend\requirements.txt .\backend\.env.example user@服务器IP:/tmp/grid-src/backend/
scp .\grid_trading_backup.sql .\uploads_backup.tar.gz user@服务器IP:/tmp/
```

> 更推荐先建 git 仓库，用 `git push` 到服务器拉取源码，避免漏传文件。

---

## 3. 服务器环境安装

### 3.1 更新系统

```bash
sudo apt update

```

### 3.2 安装基础工具

```bash
sudo apt install -y curl git unzip
```

### 3.3 安装 Python

Ubuntu 22.04 自带 Python 3.10，Ubuntu 24.04 自带 3.12，均满足要求（项目需要 3.10+）：

```bash
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

### 3.4 安装 Node.js 18+

Ubuntu 自带的 Node 可能偏旧，推荐用 NodeSource：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

### 3.5 安装 MySQL 8.0

```bash
sudo apt install -y mysql-server
sudo systemctl enable --now mysql
sudo mysql_secure_installation
```

`mysql_secure_installation` 会引导设置 root 密码、移除匿名用户等，按提示完成。

### 3.6 安装 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

### 3.7 依赖清单汇总

| 类别 | 必需依赖 | 来源 |
|------|----------|------|
| 系统包 | `python3`、`python3-venv`、`python3-pip`、`nodejs`、`npm`、`mysql-server`、`nginx`、`curl`、`git`、`unzip` | apt / NodeSource |
| 后端 Python 库 | `requirements.txt` 全部条目（FastAPI、SQLAlchemy、akshare、pymysql、alembic、python-multipart 等） | `pip install -r requirements.txt` |
| 前端 Node 库 | `package.json` 全部条目（Vue、Element Plus、ECharts、axios 等） | `npm install` |
| HTTPS 证书工具 | `certbot`、`python3-certbot-nginx` | apt（可选，启用 HTTPS 时需要） |
| 编译工具（可选） | `build-essential` | 仅当 pip 安装某些库需要本地编译时使用，常规安装一般不需要 |

> 可选编译工具按需安装：`sudo apt install -y build-essential`。

---

## 4. 代码部署

### 4.1 创建部署目录

```bash
sudo mkdir -p /opt/grid-trading
sudo chown -R $USER:$USER /opt/grid-trading
```

### 4.2 上传源码

用 scp / git 把源码放到 `/opt/grid-trading/`，最终目录结构：

```text
/opt/grid-trading/
├── backend/
├── frontend/
├── docs/
├── PRD_网格交易系统.md
├── README.md
├── start_ubuntu.sh
└── stop_ubuntu.sh
```

### 4.3 上传并解压数据文件

```bash
cp /tmp/grid_trading_backup.sql /opt/grid-trading/
tar -xzf /tmp/uploads_backup.tar.gz -C /opt/grid-trading/backend/
```

---

## 5. 数据库初始化与数据导入

### 5.1 创建数据库与专用账号

```bash
sudo mysql
```

```sql
CREATE DATABASE grid_trading DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'grid_app'@'localhost' IDENTIFIED BY '替换为强密码';
GRANT ALL PRIVILEGES ON grid_trading.* TO 'grid_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5.2 导入旧数据

```bash
mysql -u grid_app -p grid_trading < /opt/grid-trading/grid_trading_backup.sql

mysql -u grid_app -p grid_trading < /opt/grid-trading/grid_trading_backup_utf8.sql -----先转成 utf8.sql 

## 先转成 utf8.sql 
iconv -f UTF-16 -t UTF-8 \
  /opt/grid-trading/grid_trading_backup.sql \
  > /opt/grid-trading/grid_trading_backup_utf8.sql

```

> 备份文件里带 `CREATE DATABASE` 时，也可直接 `mysql -u grid_app -p < grid_trading_backup.sql`。

### 5.3 验证迁移版本

```bash
cd /opt/grid-trading/backend

先安装
sudo apt update
sudo apt install -y python3-venv python3-pip
rm -rf venv  ---删除已有的


python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
alembic current
alembic upgrade head
```

如果导入的备份版本低于代码迁移版本，`alembic upgrade head` 会自动补齐；若已是相同版本，则无需操作。

---

## 6. 后端配置与启动

### 6.1 配置环境变量

```bash
cd /opt/grid-trading/backend
cp .env.example .env
nano .env
```

关键配置：

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=grid_app
DB_PASSWORD=替换为强密码
DB_NAME=grid_trading
MARKET_DATA_MODE=real
JWT_SECRET=替换为至少32位随机字符串
```

设置权限：

```bash
chmod 600 .env
```

### 6.2 上传目录权限

```bash
mkdir -p /opt/grid-trading/backend/uploads
sudo chown -R $USER:$USER /opt/grid-trading/backend/uploads
```

### 6.3 手动启动验证

```bash
cd /opt/grid-trading/backend
source venv/bin/activate
venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```bash
curl http://127.0.0.1:8000/health
```

返回 `{"status":"ok","service":"grid-trading-system"}` 即正常。

### 6.4 systemd 常驻服务

```bash
sudo nano /etc/systemd/system/grid-backend.service
```

```ini
[Unit]
Description=Grid Trading Backend
After=network.target mysql.service

[Service]
WorkingDirectory=/opt/grid-trading/backend
ExecStart=/opt/grid-trading/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
User=ubuntu ---

[Install]
WantedBy=multi-user.target
```

> `User` 改成实际运行用户；目录权限需保证该用户可读写 `uploads`。

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable grid-backend
sudo systemctl start grid-backend
sudo systemctl status grid-backend
journalctl -u grid-backend -f
```

---

## 7. 前端构建与 Nginx

### 7.1 安装依赖并构建

```bash
cd /opt/grid-trading/frontend
npm install
npm run build
```

构建产物在 `frontend/dist`。

### 7.2 Nginx 站点配置

sudo mkdir -p  /etc/nginx/sites-available

cd /etc/nginx/sites-available/

```bash
sudo nano /etc/nginx/sites-available/grid-trading.conf
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20m;

    root /opt/grid-trading/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```



本机：（作废）

```
server {
    listen 127.0.0.1:80;
    server_name localhost;

    root /opt/grid-trading/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```



云服务器：

```
listen 80;
server_name _;   # 或直接写你的公网 IP
```

完整的如下：

```
server {
    listen 80;
    server_name _;
    
    client_max_body_size 20m;          #  加这一行，放开上传体积限制

    root /opt/grid-trading/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```



放开防火墙：`sudo ufw allow 'Nginx Full'`，



还要到腾讯云控制台，在服务器“安全组”里放行 80（和 443，如果以后上 HTTPS）。安全组是云厂商层面的防火墙，UFW 是系统层面的，两层都要放行，缺一个都访问不到。

启用并重载：

```bash
sudo ln -s /etc/nginx/sites-available/grid-trading.conf /etc/nginx/sites-enabled/
c ----如果 Nginx 自带的 default 站点还在占着 80 端口，先删掉软链
sudo nginx -t  --检查配置语法，必须输出 syntax is ok
sudo systemctl reload nginx  ---重新加载
```

### 7.3 HTTPS（推荐）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot 会自动改写 Nginx 配置并配置自动续期。

### 7.4 端口与地址配置清单

| 配置项 | 配置位置 | 说明 |
|--------|----------|------|
| 前端开发端口 5173 | `frontend/vite.config.js` 的 `server.port`；`start_ubuntu.sh` 的 `--port 5173` | 开发模式页面端口 |
| 前端请求后端地址 | `frontend/src/api/index.js` 中 `baseURL: '/api'` | 生产同域部署无需修改，请求自动经 Nginx |
| 开发环境接口代理 | `frontend/vite.config.js` 的 `proxy`：`/api`、`/uploads` → `http://127.0.0.1:8000` | 仅在 vite dev 模式生效 |
| 后端监听地址/端口 | `start_ubuntu.sh`、systemd `ExecStart`、uvicorn 的 `--host 127.0.0.1 --port 8000` | 后端固定监听本机 8000 |
| 数据库连接 | `backend/.env`：`DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME` | 服务器上按实际 MySQL 账号修改 |
| CORS 白名单 | `backend/app/main.py` 的 `allow_origins` | 同域部署无需改动；前后端跨域时才需要加入实际前端地址 |
| 生产访问入口 | Nginx：`server_name` + 80/443，`root frontend/dist`，`/api`、`/uploads` 反代 8000 | 用户浏览器访问的地址 |

> 生产环境不需要修改前端里的后端地址：页面和接口同域，`/api` 自动由 Nginx 转发到后端 8000。

---

## 8. 防火墙与安全

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

其他建议：

- MySQL 只监听本机：确认 `/etc/mysql/mysql.conf.d/mysqld.cnf` 中 `bind-address = 127.0.0.1`；
- 后端只监听 127.0.0.1，不对外暴露 8000；
- `.env` 权限 600，数据库密码使用强密码；
- 定期备份数据库与 `uploads`。

---

## 9. 上线验证清单

1. `curl http://127.0.0.1:8000/health` 返回 ok；
2. 浏览器访问 `http://your-domain.com`，登录页正常、页脚参数展示；
3. 登录 / 注册 / 修改密码正常；
4. 策略管理、监控、收益分析原功能正常；
5. 公告后台可上传图片，前台展示图片与名称，停用后前台不显示；
6. 文档管理可上传、下载、PDF/图片预览，停用后操作手册页不显示；
7. 模拟回测可创建策略、发起回测，行情接口异常时自动降级并显示提示；
8. 检查 `journalctl -u grid-backend` 与 `nginx -t` 无错误。

---

## 10. 备份与回滚

### 10.1 数据库定时备份

```bash
sudo crontab -e
```

```cron
0 2 * * * mysqldump -u grid_app -p'密码' grid_trading --single-transaction > /opt/backup/grid_$(date +\%Y\%m\%d).sql
```

### 10.2 上传目录备份

```bash
tar -czf /opt/backup/uploads_$(date +%Y%m%d).tar.gz -C /opt/grid-trading/backend uploads
```

### 10.3 回滚

- 代码回滚：保留上一版目录，如 `/opt/grid-trading-backup`，改 Nginx/systemd 指向旧目录后重启；
- 数据回滚：用备份 SQL 恢复 `mysql -u grid_app -p grid_trading < 备份.sql`；
- 服务回滚：`sudo systemctl stop grid-backend && sudo systemctl start grid-backend`。

cd /opt/grid-trading

启动命名：

```
chmod +x start_ubuntu.sh # 文件授权

chmod +x stop_ubuntu.sh


```

```
sudo ./start_ubuntu.sh
sudo ./stop_ubuntu.sh

```



迁移后，密码不对

curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"管理员密码"}'

curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"普通用户账号","password":"普通用户密码"}'
