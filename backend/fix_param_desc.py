import pymysql

from app.core.config import settings

conn = pymysql.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
    charset="utf8mb4",
    connect_timeout=5,
)
cur = conn.cursor()

updates = {
    "account_expire_days": "新注册用户账号有效天数，到期后需管理员续期",
    "scheduler_enabled": "监控定时任务总开关：1 启用，0 停用",
    "scheduler_interval_minutes": "监控定时任务轮询间隔（分钟），个股/ETF 行情检查频率",
    "email_smtp_host": "邮件发件 SMTP 服务器地址，用于发送价格触发等邮件提醒",
    "email_smtp_port": "邮件发件 SMTP 端口：SSL 常用 465，TLS 常用 587",
    "email_smtp_user": "邮件发件邮箱账号",
    "email_smtp_password": "邮件发件邮箱授权码或密码，仅管理员可见，不回显",
    "email_from_email": "邮件发件人地址，邮件提醒中展示的发件邮箱",
    "email_enabled": "邮件提醒总开关：1 启用，0 停用",
    "footer_copyright": "登录页页脚版权信息文字，例如 Copyright © 2026 网格交易系统",
    "footer_icp": "登录页页脚展示的备案号，为空时不显示",
    "footer_support": "登录页页脚展示的技术支持或联系方式，为空时不显示",
    "footer_version": "登录页页脚展示的系统版本信息，为空时不显示",
}

for key, desc in updates.items():
    cur.execute(
        "UPDATE system_param SET description=%s WHERE param_key=%s",
        (desc, key),
    )
conn.commit()

cur.execute("SELECT param_key, description FROM system_param ORDER BY param_key")
for key, desc in cur.fetchall():
    print(key, "=>", (desc or "").encode("unicode_escape").decode())
cur.close()
conn.close()
