from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import os

# 数据库配置 - 优先从环境变量读取（ClawCloud 部署用）
# 本地开发可通过环境变量覆盖为 AlwaysData
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'quicknews-db-mysql.ns-czp73szj.svc'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 't958gtbz'),
    'database': os.environ.get('DB_NAME', 'quicknews_maindb'),
}

def get_engine():
    """创建数据库连接引擎"""
    connection_string = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['database']}"
    )
    
    print(f"[DB] 连接: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            'charset': 'utf8mb4',
            'init_command': "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        }
    )
    return engine

engine = get_engine()

def test_connection():
    """测试数据库连接并检查 Event Scheduler"""
    try:
        conn = engine.connect()
        result = conn.execute(text("SELECT 'Connected!', NOW(), DATABASE(), VERSION(), @@event_scheduler"))
        row = result.fetchone()
        print(f"[DB Test] 状态: {row[0]}")
        print(f"[DB Test] 时间: {row[1]}")
        print(f"[DB Test] 数据库: {row[2]}")
        print(f"[DB Test] 版本: {row[3]}")
        print(f"[DB Test] Event Scheduler: {row[4]}")
        
        # 如果 Event Scheduler 关闭，打印警告
        if row[4] != 'ON':
            print("[DB Test] ⚠️ 警告: Event Scheduler 未开启，将依赖 Python 定时任务")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Test] 连接失败: {e}")
        return False
