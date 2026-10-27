from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库连接
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "grid_app"
    db_password: str = ""
    db_name: str = "grid_trading"

    # 行情模式：mock / real
    market_data_mode: str = "mock"

    # 推送 Webhook（可选）
    dingtalk_webhook: str = ""
    wechat_webhook: str = ""

    # JWT 签名密钥。生产环境必须通过环境变量设置。
    jwt_secret: str = ""

    # 服务监听地址
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
