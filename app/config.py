from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, String, JSON, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from app.log_config import setup_logger

# 设置日志
logger = setup_logger(__name__)

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost/model_switcher")

# SQLAlchemy设置
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 超过pool_size后最多可以创建的连接数
    pool_timeout=30,  # 连接池中没有可用连接时的等待时间
    pool_recycle=3600  # 连接在连接池中重复使用的时间限制
)

# 添加数据库连接池事件监听
@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug('Database connection checked out from pool')

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    logger.debug('Database connection returned to pool')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChannelConfig(BaseModel):
    base_url: str
    api_key: str
    model: Optional[str] = None

class AppConfig(BaseModel):
    channels: Dict[str, ChannelConfig]
    current_channel: str
    current_model: str
    api_key: str

# 数据库模型
class ConfigTable(Base):
    __tablename__ = "config"
    
    id = Column(String(50), primary_key=True, default="default")
    channels = Column(JSON, nullable=False)
    current_channel = Column(String(50), nullable=False)
    current_model = Column(String(50), nullable=False)
    api_key = Column(String(255), nullable=False)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConfigManager:
    _instance = None
    _config: AppConfig = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            Base.metadata.create_all(bind=engine)
            self._load_config()
            self._initialized = True
    
    def _load_config(self) -> None:
        logger.info("开始加载配置...")
        try:
            with get_db() as db:
                config_record = db.query(ConfigTable).filter_by(id="default").first()
                if not config_record:
                    logger.info("未找到现有配置，创建默认配置...")
                    config_data = self._create_default_config()
                else:
                    logger.info("找到现有配置，正在加载...")
                    # 将存储的字典转换回ChannelConfig对象
                    channels = {
                        name: ChannelConfig(**channel_data)
                        for name, channel_data in config_record.channels.items()
                    }
                    config_data = {
                        "channels": channels,
                        "current_channel": config_record.current_channel,
                        "current_model": config_record.current_model,
                        "api_key": config_record.api_key
                    }
                self._config = AppConfig(**config_data)
                logger.info("配置加载完成")
        except Exception as e:
            logger.error(f"配置加载失败: {str(e)}")
            raise ConfigError(f"配置加载失败: {str(e)}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        logger.info("创建默认配置...")
        default_config = {
            "channels": {
                "default": {
                    "base_url": os.getenv("DEFAULT_BASE_URL"),
                    "api_key": os.getenv("DEFAULT_API_KEY"),
                    "model": os.getenv("DEFAULT_MODEL"),
                }
            },
            "current_channel": "default",
            "current_model": "gpt-4",
            "api_key": os.getenv("DEFAULT_API_KEY")
        }
        
        try:
            with get_db() as db:
                config_record = ConfigTable(
                    id="default",
                    channels=default_config["channels"],
                    current_channel=default_config["current_channel"],
                    current_model=default_config["current_model"],
                    api_key=default_config["api_key"]
                )
                db.add(config_record)
                db.commit()
                logger.info("默认配置创建并保存成功")
        except Exception as e:
            logger.error(f"创建默认配置失败: {str(e)}")
            raise
        
        return default_config
    
    def save_config(self) -> None:
        logger.info("开始保存配置...")
        try:
            with get_db() as db:
                config_record = db.query(ConfigTable).filter_by(id="default").first()
                if config_record:
                    # 将ChannelConfig对象转换为字典，如果已经是字典则直接使用
                    channels_dict = {
                        name: channel.dict() if isinstance(channel, ChannelConfig) else channel
                        for name, channel in self._config.channels.items()
                    }
                    config_record.channels = channels_dict
                    config_record.current_channel = self._config.current_channel
                    config_record.current_model = self._config.current_model
                    config_record.api_key = self._config.api_key
                    db.commit()
                    logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"配置保存失败: {str(e)}")
            raise ConfigError(f"配置保存失败: {str(e)}")
    
    @property
    def config(self) -> AppConfig:
        return self._config
    
    def get_current_channel_config(self) -> ChannelConfig:
        return self._config.channels[self._config.current_channel]
    
    def update_current_model(self, model: str) -> None:
        logger.info(f"更新当前模型为: {model}")
        self._config.current_model = model
        self.save_config()
    
    def update_current_channel(self, channel: str) -> None:
        logger.info(f"尝试更新当前通道为: {channel}")
        if channel not in self._config.channels:
            logger.error(f"通道 {channel} 不存在")
            raise ConfigError(f"通道 {channel} 不存在")
        self._config.current_channel = channel
        self.save_config()

class ConfigError(Exception):
    """配置相关错误的自定义异常类"""
    pass
